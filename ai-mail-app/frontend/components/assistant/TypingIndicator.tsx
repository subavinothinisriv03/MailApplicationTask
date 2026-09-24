/** Typing indicator animation component. */
import React from "react";

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center space-x-1.5 p-3 rounded-2xl bg-zinc-100 dark:bg-zinc-800 text-zinc-500 max-w-[80px]">
      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:-0.3s]" />
      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:-0.15s]" />
      <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
    </div>
  );
};
