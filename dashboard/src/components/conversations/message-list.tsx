"use client";

import type { MessageItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface MessageListProps {
  messages: MessageItem[];
}

function formatTime(dateStr: string) {
  const date = new Date(dateStr + "Z");
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No messages in this channel.
      </p>
    );
  }

  // Debug: Log messages to identify interaction_type values
  messages.forEach((msg, i) => {
    if (msg.interaction_type) {
      console.log(`Message ${i}: interaction_type="${msg.interaction_type}", role="${msg.role}"`);
    }
  });

  return (
    <div className="space-y-3">
      {messages.map((msg, i) => {
        const isUser = msg.role === "user";
        const isCodeReview = msg.interaction_type === "code_review";
        return (
          <div
            key={i}
            className={`flex ${isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-lg px-4 py-2 ${
                isUser
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <div className={`mt-1 flex flex-wrap items-center gap-2 text-xs ${isUser ? "opacity-70" : "text-muted-foreground"}`}>
                <span>{formatTime(msg.created_at)}</span>
                {isCodeReview && !isUser && (
                  <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100">
                    Code Review
                  </Badge>
                )}
                {msg.provider && !isUser && (
                  <Badge variant="outline" className="text-xs px-1.5 py-0">
                    {msg.provider}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
