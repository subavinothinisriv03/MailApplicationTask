/** Chat message bubble component with tool action indicators. */
import React from "react";
import { ChatMessage as ChatMessageType } from "@/lib/types";
import { ToolActionIndicator } from "./ToolActionIndicator";
import { Bot, User as UserIcon } from "lucide-react";

interface Props {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div className={`flex max-w-[85%] space-x-2.5 ${isUser ? "flex-row-reverse space-x-reverse" : "flex-row"}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
            isUser
              ? "bg-blue-600 text-white shadow-sm"
              : "bg-zinc-800 text-blue-400 border border-zinc-700 shadow-sm"
          }`}
        >
          {isUser ? <UserIcon className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
        </div>

        {/* Bubble Content */}
        <div className="flex flex-col space-y-1.5">
          <div
            className={`p-3.5 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
              isUser
                ? "bg-blue-600 text-white rounded-tr-sm shadow-md"
                : "bg-zinc-100 dark:bg-zinc-800/90 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700/60 rounded-tl-sm shadow-sm"
            }`}
          >
            {message.content}
          </div>

          {/* Render Tool Actions executed in this turn */}
          {message.tool_actions && message.tool_actions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-0.5">
              {message.tool_actions.map((act, idx) => (
                <ToolActionIndicator key={idx} action={act} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
