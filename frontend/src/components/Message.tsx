"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SourceCard } from "./SourceCard";
import { User, Bot } from "lucide-react";
import type { Source } from "@/lib/api";

export interface MessageData {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  subQueries?: string[];
  streaming?: boolean;
}

export function Message({ msg }: { msg: MessageData }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        {isUser ? (
          <div className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm">
            {msg.content}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-slate-800 border border-slate-700 px-4 py-3 rounded-2xl rounded-tl-sm">
              {msg.streaming && !msg.content ? (
                <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse rounded-sm" />
              ) : (
                <div className="prose text-slate-200 text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              )}
              {msg.streaming && msg.content && (
                <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse rounded-sm ml-0.5 align-middle" />
              )}
            </div>

            {msg.subQueries && msg.subQueries.length > 1 && (
              <div className="px-1">
                <p className="text-xs text-slate-500 mb-1">Searched for:</p>
                <div className="flex flex-wrap gap-1">
                  {msg.subQueries.map((q, i) => (
                    <span key={i} className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700">
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {msg.sources && msg.sources.length > 0 && (
              <div className="px-1">
                <p className="text-xs text-slate-500 mb-1.5">Sources:</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {msg.sources.map((s, i) => <SourceCard key={i} source={s} index={i} />)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
          <User className="w-4 h-4 text-slate-300" />
        </div>
      )}
    </div>
  );
}
