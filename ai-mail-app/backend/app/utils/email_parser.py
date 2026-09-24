"""Utilities for parsing Gmail API message objects and building RFC 2822 messages."""
import base64
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formatdate
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def decode_mime_header(header_value: Optional[str]) -> str:
    """Decodes MIME encoded header strings."""
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            result.append(fragment.decode(encoding or "utf-8", errors="replace"))
        else:
            result.append(str(fragment))
    return "".join(result)


def parse_address_list(address_header: Optional[str]) -> List[str]:
    """Parse comma-separated address list into clean email strings."""
    if not address_header:
        return []
    addresses = []
    for part in address_header.split(","):
        name, addr = parseaddr(part.strip())
        if addr:
            addresses.append(addr)
        elif part.strip():
            addresses.append(part.strip())
    return addresses


def parse_gmail_message(gmail_msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a Gmail API message resource into a dictionary ready for the Email model.
    """
    msg_id = gmail_msg.get("id")
    thread_id = gmail_msg.get("threadId")
    snippet = gmail_msg.get("snippet", "")
    label_ids = gmail_msg.get("labelIds", [])
    internal_date_ms = gmail_msg.get("internalDate")

    if internal_date_ms:
        try:
            received_at = datetime.utcfromtimestamp(int(internal_date_ms) / 1000.0)
        except Exception:
            received_at = datetime.utcnow()
    else:
        received_at = datetime.utcnow()

    payload = gmail_msg.get("payload", {})
    headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}

    # Extract headers
    raw_from = headers.get("from", "")
    sender_name, sender_email = parseaddr(raw_from)
    sender_name = decode_mime_header(sender_name) or sender_name or sender_email

    subject = decode_mime_header(headers.get("subject", "(No Subject)"))
    recipients = parse_address_list(headers.get("to", ""))
    cc = parse_address_list(headers.get("cc", ""))
    bcc = parse_address_list(headers.get("bcc", ""))

    # Extract body & attachments metadata
    body_text, body_html, attachments = extract_body_and_attachments(payload)
    final_body = body_text if body_text.strip() else body_html
    if not final_body.strip():
        final_body = snippet

    is_read = "UNREAD" not in label_ids
    is_starred = "STARRED" in label_ids
    is_sent = "SENT" in label_ids

    return {
        "gmail_id": msg_id,
        "thread_id": thread_id,
        "sender": sender_email or raw_from,
        "sender_name": sender_name,
        "recipients": recipients,
        "cc": cc,
        "bcc": bcc,
        "subject": subject,
        "body": final_body,
        "snippet": snippet,
        "is_read": is_read,
        "is_starred": is_starred,
        "is_sent": is_sent,
        "labels": label_ids,
        "received_at": received_at,
        "attachments": attachments
    }


def extract_body_and_attachments(payload: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Recursively traverses Gmail payload parts to extract plain text, HTML, and attachment metadata."""
    body_text = ""
    body_html = ""
    attachments = []

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    filename = payload.get("filename", "")

    if filename and payload.get("body", {}).get("attachmentId"):
        attachments.append({
            "filename": filename,
            "mimeType": mime_type,
            "size": payload.get("body", {}).get("size", 0),
            "attachmentId": payload.get("body", {}).get("attachmentId")
        })

    if body_data:
        try:
            # Gmail uses URL-safe base64
            decoded_bytes = base64.urlsafe_b64decode(body_data + "==")
            decoded_str = decoded_bytes.decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                body_text += decoded_str
            elif mime_type == "text/html":
                body_html += decoded_str
            else:
                body_text += decoded_str
        except Exception:
            pass

    for part in payload.get("parts", []):
        sub_text, sub_html, sub_attachments = extract_body_and_attachments(part)
        if sub_text:
            body_text += "\n" + sub_text
        if sub_html:
            body_html += "\n" + sub_html
        attachments.extend(sub_attachments)

    return body_text.strip(), body_html.strip(), attachments


def create_rfc2822_message(
    sender: str,
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    thread_id: Optional[str] = None,
    in_reply_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates an RFC 2822 MIME message formatted and base64url encoded for Gmail API send endpoint.
    """
    message = MIMEMultipart("alternative")
    message["From"] = sender
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)

    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to

    # Plain text and HTML parts
    part_text = MIMEText(body, "plain", "utf-8")
    message.attach(part_text)

    # Simple HTML conversion for rich mail client rendering
    html_content = body.replace("\n", "<br>")
    part_html = MIMEText(f"<div style='font-family: sans-serif; font-size: 14px;'>{html_content}</div>", "html", "utf-8")
    message.attach(part_html)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    result: Dict[str, Any] = {"raw": raw}
    if thread_id:
        result["threadId"] = thread_id

    return result
