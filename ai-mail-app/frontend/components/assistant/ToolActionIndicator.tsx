/** Visual feedback for UI actions triggered by the AI agent. */
import React from "react";
import { ToolAction } from "@/lib/types";
import { Navigation, Edit3, Search, Mail, Send, Reply, CheckCircle2 } from "lucide-react";

interface Props {
  action: ToolAction;
}

export const ToolActionIndicator: React.FC<Props> = ({ action }) => {
  const getToolDetails = (tool: string) => {
    switch (tool) {
      case "navigate_to_compose":
        return {
          icon: <Navigation className="w-4 h-4 text-blue-500 animate-pulse" />,
          label: "Navigating to Compose view",
          color: "border-blue-500/30 bg-blue-500/10 text-blue-400",
        };
      case "fill_compose_form":
        return {
          icon: <Edit3 className="w-4 h-4 text-emerald-500 animate-pulse" />,
          label: "Typing form fields (To, Subject, Body)",
          color: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
        };
      case "search_emails":
        return {
          icon: <Search className="w-4 h-4 text-amber-500 animate-pulse" />,
          label: `Filtering emails: ${action.arguments.query || "date/folder"}`,
          color: "border-amber-500/30 bg-amber-500/10 text-amber-400",
        };
      case "open_email":
        return {
          icon: <Mail className="w-4 h-4 text-purple-500 animate-pulse" />,
          label: `Opening email ID: ${action.arguments.email_id}`,
          color: "border-purple-500/30 bg-purple-500/10 text-purple-400",
        };
      case "reply_to_email":
        return {
          icon: <Reply className="w-4 h-4 text-indigo-500 animate-pulse" />,
          label: "Generating context-aware reply",
          color: "border-indigo-500/30 bg-indigo-500/10 text-indigo-400",
        };
      case "send_email":
        return {
          icon: <Send className="w-4 h-4 text-rose-500 animate-pulse" />,
          label: "Sending email via Gmail API",
          color: "border-rose-500/30 bg-rose-500/10 text-rose-400",
        };
      default:
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-zinc-400" />,
          label: `Executing tool: ${tool}`,
          color: "border-zinc-500/30 bg-zinc-500/10 text-zinc-400",
        };
    }
  };

  const details = getToolDetails(action.tool);

  return (
    <div
      className={`flex items-center space-x-2 text-xs px-2.5 py-1.5 rounded-lg border shadow-sm transition-all duration-300 ${details.color}`}
    >
      {details.icon}
      <span className="font-medium">{details.label}</span>
    </div>
  );
};
