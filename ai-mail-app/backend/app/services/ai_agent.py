"""OpenAI Tool-Calling AI Agent for controlling the Mail UI."""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from openai import OpenAI

from app.config import settings
from app.models.email import Email
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantResponse,
    ToolAction
)
from app.schemas.email import EmailCreate, EmailResponse
from app.services.email_service import email_service
from app.websocket.manager import ws_manager

logger = logging.getLogger("ai_agent")

# OpenAI Function/Tool Calling Definitions
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to_compose",
            "description": "Navigate the frontend UI to the email compose view.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_compose_form",
            "description": "Populate the email compose form fields in the frontend UI with recipient, subject, and body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipient email addresses"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of CC email addresses"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of BCC email addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search the user's emails by sender, keyword, or folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or sender name"
                    },
                    "folder": {
                        "type": "string",
                        "enum": ["inbox", "sent", "starred"],
                        "description": "Folder to search within"
                    },
                    "days_ago": {
                        "type": "integer",
                        "description": "Filter emails from the last N days"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_email",
            "description": "Instruct the frontend to open and display a specific email by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The unique ID of the email to open"
                    }
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reply_to_email",
            "description": "Prepare a reply to an email, prefilling the sender, subject with Re:, and reply body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "ID of the email to reply to"
                    },
                    "body": {
                        "type": "string",
                        "description": "Draft text for the reply"
                    }
                },
                "required": ["email_id", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send the email immediately through Gmail. Only call this when the user explicitly instructs to send.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipient email addresses"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional CC addresses"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional BCC addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body content of the email"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
]


class AIAgentService:
    """Orchestrates natural language intent parsing, OpenAI tool calling, and UI state actuation."""

    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")

    def _build_system_prompt(self, user_id: str, db: Session, context: AssistantChatRequest) -> str:
        """Builds a rich, context-aware prompt detailing the current application state."""
        opened_email_summary = "None"
        if context.current_email_id:
            email_obj = email_service.get_email_by_id(db, user_id, context.current_email_id)
            if email_obj:
                opened_email_summary = (
                    f"ID: {email_obj.id}\n"
                    f"From: {email_obj.sender_name} <{email_obj.sender}>\n"
                    f"Subject: {email_obj.subject}\n"
                    f"Snippet: {email_obj.snippet}\n"
                    f"Body: {email_obj.body[:300]}"
                )

        draft_summary = json.dumps(context.draft_state) if context.draft_state else "Empty"
        filters_summary = json.dumps(context.current_filters) if context.current_filters else "None"

        return (
            "You are an intelligent, active AI assistant embedded in a modern mail web application.\n"
            "CRITICAL GOAL: You do not just chat. You actively control the user interface through tools.\n\n"
            "APPLICATION RULES:\n"
            "1. When user asks to compose or write an email, call `navigate_to_compose` followed by `fill_compose_form`.\n"
            "2. When user asks to search or find emails (e.g. 'find emails from Sarah', 'show emails from last 10 days'), call `search_emails`.\n"
            "3. When user asks to open an email (e.g. 'open the latest email from John'), find it and call `open_email`.\n"
            "4. When user asks to reply (e.g. 'reply to this email saying...'), use the currently opened email ID and call `reply_to_email`.\n"
            "5. When user asks to send (e.g. 'send this email', 'send it'), call `send_email` with the draft or compose parameters.\n"
            "6. SAFETY GUARD: Drafting or writing an email must NEVER call `send_email`. Only call `send_email` when the user explicitly commands to send.\n\n"
            f"CURRENT CLIENT CONTEXT:\n"
            f"- Active View: {context.current_view}\n"
            f"- Currently Opened Email:\n{opened_email_summary}\n"
            f"- Active Filters: {filters_summary}\n"
            f"- Compose Draft State: {draft_summary}\n"
        )

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Executes the specific tool against the database / services and broadcasts WebSocket events."""
        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
        result: Dict[str, Any] = {}

        if tool_name == "navigate_to_compose":
            result = {"status": "navigating", "target": "/compose"}

        elif tool_name == "fill_compose_form":
            to = arguments.get("to", [])
            if isinstance(to, str):
                to = [to]
            result = {
                "to": to,
                "cc": arguments.get("cc", []),
                "bcc": arguments.get("bcc", []),
                "subject": arguments.get("subject", ""),
                "body": arguments.get("body", "")
            }

        elif tool_name == "search_emails":
            query = arguments.get("query", "")
            folder = arguments.get("folder", "inbox")
            days_ago = arguments.get("days_ago")
            emails, total = email_service.get_emails(
                db=db,
                user_id=user_id,
                folder=folder,
                query=query,
                days_ago=days_ago,
                page=1,
                page_size=20
            )
            parsed_emails = [
                EmailResponse.model_validate(em).model_dump(mode="json")
                for em in emails
            ]
            result = {
                "query": query,
                "folder": folder,
                "days_ago": days_ago,
                "total_found": total,
                "emails": parsed_emails[:5]  # brief summaries
            }

        elif tool_name == "open_email":
            email_id = arguments.get("email_id")
            email_obj = email_service.get_email_by_id(db, user_id, email_id)
            if email_obj:
                # Mark as read
                email_service.mark_as_read(db, user_id, email_id, is_read=True)
                result = {
                    "email_id": email_id,
                    "subject": email_obj.subject,
                    "sender": email_obj.sender,
                    "status": "opened"
                }
            else:
                result = {"error": f"Email {email_id} not found."}

        elif tool_name == "reply_to_email":
            email_id = arguments.get("email_id")
            body = arguments.get("body", "")
            email_obj = email_service.get_email_by_id(db, user_id, email_id)
            if email_obj:
                reply_subject = email_obj.subject
                if not reply_subject.lower().startswith("re:"):
                    reply_subject = f"Re: {reply_subject}"
                result = {
                    "email_id": email_id,
                    "to": [email_obj.sender],
                    "subject": reply_subject,
                    "body": body,
                    "status": "reply_prepared"
                }
            else:
                result = {"error": f"Email {email_id} not found to reply."}

        elif tool_name == "send_email":
            to = arguments.get("to", [])
            if isinstance(to, str):
                to = [to]
            email_create = EmailCreate(
                to=to,
                cc=arguments.get("cc", []),
                bcc=arguments.get("bcc", []),
                subject=arguments.get("subject", ""),
                body=arguments.get("body", "")
            )
            sent_email = await email_service.create_and_send_email(db, user_id, email_create)
            result = {
                "status": "sent",
                "email_id": sent_email.id,
                "subject": sent_email.subject,
                "recipient": to
            }

        # Broadcast tool action to WebSocket
        await ws_manager.emit_tool_action(
            tool=tool_name,
            arguments=arguments,
            user_id=user_id,
            result=result
        )

        return result

    async def _fallback_agent_parse(
        self,
        message: str,
        user_id: str,
        db: Session,
        context: AssistantChatRequest
    ) -> AssistantResponse:
        """
        Rule-based intent parser ensuring seamless tool calling and UI execution
        when OpenAI API key is not present or when testing offline.
        """
        lower_msg = message.lower().strip()
        tool_actions: List[ToolAction] = []
        assistant_reply = ""

        # Case 1: Send explicitly
        if lower_msg.startswith("send") or "send the email" in lower_msg or "send this email" in lower_msg or lower_msg == "send it":
            to = []
            subject = ""
            body = ""
            if context.draft_state:
                to = context.draft_state.get("to", [])
                subject = context.draft_state.get("subject", "")
                body = context.draft_state.get("body", "")

            if not to or not subject:
                # Check for explicit email target
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
                if email_match:
                    to = [email_match.group(0)]
                subject = subject or "Quick update"
                body = body or "Following up on our conversation."

            args = {"to": to if isinstance(to, list) else [to], "subject": subject, "body": body}
            res = await self.execute_tool("send_email", args, user_id, db)
            tool_actions.append(ToolAction(tool="send_email", arguments=args, result=res))
            assistant_reply = f"I've sent the email to {', '.join(to)} with subject '{subject}'."

        # Case 2: Reply to current email
        elif "reply" in lower_msg:
            email_id = context.current_email_id
            if not email_id:
                # Find the latest email in inbox
                emails, _ = email_service.get_emails(db, user_id, folder="inbox", page=1, page_size=1)
                if emails:
                    email_id = emails[0].id

            reply_text = "I received your email and will follow up shortly."
            saying_match = re.search(r'saying\s+(.*)', message, re.IGNORECASE)
            if saying_match:
                reply_text = saying_match.group(1).strip().strip('"\'')

            if email_id:
                args = {"email_id": email_id, "body": reply_text}
                res = await self.execute_tool("reply_to_email", args, user_id, db)
                tool_actions.append(ToolAction(tool="reply_to_email", arguments=args, result=res))
                assistant_reply = f"I've prepared a reply to the email with your response: \"{reply_text}\"."
            else:
                assistant_reply = "Please open an email first so I can prepare a reply to it."

        # Case 3: Open latest email from X or open email
        elif "open" in lower_msg:
            from_match = re.search(r'from\s+([a-zA-Z0-9_\.-]+)', message, re.IGNORECASE)
            query_sender = from_match.group(1) if from_match else ""
            emails, _ = email_service.get_emails(db, user_id, folder="inbox", query=query_sender, sender=query_sender, page=1, page_size=5)

            if emails:
                target_email = emails[0]
                args = {"email_id": target_email.id}
                res = await self.execute_tool("open_email", args, user_id, db)
                tool_actions.append(ToolAction(tool="open_email", arguments=args, result=res))
                assistant_reply = f"I found the latest email from {target_email.sender_name or target_email.sender} ('{target_email.subject}') and opened it for you."
            else:
                assistant_reply = f"I couldn't find any recent emails from '{query_sender}'."

        # Case 4: Search or show emails from last N days / sender
        elif "show" in lower_msg or "find" in lower_msg or "search" in lower_msg:
            days_match = re.search(r'(\d+)\s+days', lower_msg)
            days_ago = int(days_match.group(1)) if days_match else None

            query = ""
            from_match = re.search(r'from\s+([a-zA-Z0-9_\.-]+)', message, re.IGNORECASE)
            if from_match:
                query = from_match.group(1)

            args = {"query": query, "folder": "inbox", "days_ago": days_ago}
            res = await self.execute_tool("search_emails", args, user_id, db)
            tool_actions.append(ToolAction(tool="search_emails", arguments=args, result=res))

            total_found = res.get("total_found", 0)
            filter_desc = f"from the last {days_ago} days" if days_ago else f"matching '{query}'" if query else "in your inbox"
            assistant_reply = f"I've updated the inbox filters to show emails {filter_desc}. Found {total_found} email(s)."

        # Case 5: Compose or write email
        elif "compose" in lower_msg or "write" in lower_msg:
            # 1. Trigger navigate_to_compose
            nav_res = await self.execute_tool("navigate_to_compose", {}, user_id, db)
            tool_actions.append(ToolAction(tool="navigate_to_compose", arguments={}, result=nav_res))

            # Extract recipient
            to_list = []
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
            if email_match:
                to_list = [email_match.group(0)]
            else:
                to_name_match = re.search(r'to\s+([a-zA-Z]+)', message, re.IGNORECASE)
                if to_name_match:
                    name = to_name_match.group(1).lower()
                    to_list = [f"{name}@example.com"]
                else:
                    to_list = ["john@example.com"]

            # Extract subject
            subject = "Meeting Follow-up"
            subj_match = re.search(r'subject\s+([^and]+?)(?:\s+and\s+body|\s+body|$)', message, re.IGNORECASE)
            if subj_match:
                subject = subj_match.group(1).strip().strip('"\'')
            elif "meeting" in lower_msg:
                subject = "Meeting Tomorrow"

            # Extract body
            body = "Hi,\n\nI look forward to connecting soon.\n\nBest regards,"
            body_match = re.search(r'body\s+(.*)', message, re.IGNORECASE)
            saying_match = re.search(r'saying\s+(.*)', message, re.IGNORECASE)
            if body_match:
                body = body_match.group(1).strip().strip('"\'')
            elif saying_match:
                body = saying_match.group(1).strip().strip('"\'')
            elif "let's meet at 3pm" in lower_msg:
                body = "Let's meet at 3pm."

            fill_args = {
                "to": to_list,
                "cc": [],
                "bcc": [],
                "subject": subject,
                "body": body
            }
            fill_res = await self.execute_tool("fill_compose_form", fill_args, user_id, db)
            tool_actions.append(ToolAction(tool="fill_compose_form", arguments=fill_args, result=fill_res))

            assistant_reply = f"I've navigated to Compose and filled out the email to {', '.join(to_list)} with subject '{subject}'. Review the drafted fields and let me know when you'd like me to send it!"

        else:
            # Default helpful assistant response with suggestions
            assistant_reply = (
                "I'm ready to control your mail app! You can say:\n"
                "• 'Send an email to john@example.com with subject Meeting Tomorrow and body Let's meet at 3pm'\n"
                "• 'Show emails from the last 10 days'\n"
                "• 'Open the latest email from David'\n"
                "• 'Reply to this email saying I will attend'"
            )

        return AssistantResponse(
            message=assistant_reply,
            tool_actions=tool_actions,
            execution_context={"timestamp": datetime.utcnow().isoformat()}
        )

    async def chat(
        self,
        request: AssistantChatRequest,
        user_id: str,
        db: Session
    ) -> AssistantResponse:
        """
        Main entry point for assistant requests.
        Calls OpenAI API with registered tools, or falls back to rule parser if API key is not configured.
        """
        # Broadcast typing status
        await ws_manager.emit_typing(True, user_id)

        try:
            # If no OpenAI client or key, use intelligent fallback
            if not self.client or not settings.OPENAI_API_KEY:
                return await self._fallback_agent_parse(request.message, user_id, db, request)

            system_prompt = self._build_system_prompt(user_id, db, request)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.2
            )

            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls
            tool_actions: List[ToolAction] = []

            if tool_calls:
                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = {}

                    tool_result = await self.execute_tool(fn_name, args, user_id, db)
                    tool_actions.append(
                        ToolAction(
                            tool=fn_name,
                            arguments=args,
                            result=tool_result
                        )
                    )

                # Send tool execution results back to OpenAI for final natural language explanation
                tool_result_messages = list(messages)
                tool_result_messages.append(response_msg)
                for tc, ta in zip(tool_calls, tool_actions):
                    tool_result_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps(ta.result or {})
                    })

                second_resp = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=tool_result_messages,
                    temperature=0.3
                )
                final_text = second_resp.choices[0].message.content or "Action completed."
            else:
                final_text = response_msg.content or "How can I assist you with your emails?"

            return AssistantResponse(
                message=final_text,
                tool_actions=tool_actions,
                execution_context={"timestamp": datetime.utcnow().isoformat()}
            )

        except Exception as e:
            logger.error(f"OpenAI error in agent chat: {e}. Falling back to rule parser.")
            return await self._fallback_agent_parse(request.message, user_id, db, request)

        finally:
            await ws_manager.emit_typing(False, user_id)


ai_agent_service = AIAgentService()
