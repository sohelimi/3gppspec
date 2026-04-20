"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, Radio, ChevronDown } from "lucide-react";
import { Message, type MessageData } from "@/components/Message";
import { streamChat, type Source } from "@/lib/api";

const SUGGESTIONS = [
  "What is 5G NR numerology and subcarrier spacing options?",
  "Explain the 5G standalone vs non-standalone architecture.",
  "What are the key features introduced in 3GPP Release 18?",
  "How does beam management work in 5G NR?",
  "What security mechanisms protect the 5G core network?",
];

export default function Home() {
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = useCallback(async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: MessageData = { role: "user", content: question };
    const assistantMsg: MessageData = { role: "assistant", content: "", streaming: true };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setInput("");
    setLoading(true);

    try {
      let fullText = "";
      const msgIndex = (prev: MessageData[]) => prev.length - 1;

      const updateSources = (sources: Source[], subQueries: string[]) => {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            sources,
            subQueries,
            streaming: false,
          };
          return updated;
        });
      };

      for await (const token of streamChat(question, updateSources)) {
        fullText += token;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: fullText,
          };
          return updated;
        });
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          streaming: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Radio className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100">3gppSpec</h1>
            <p className="text-xs text-slate-400">3GPP AI Assistant · Powered by Gemini</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-400">Online</span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12 space-y-6">
              <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center mx-auto">
                <Radio className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-100 mb-2">Ask about 3GPP Standards</h2>
                <p className="text-slate-400 text-sm max-w-md mx-auto">
                  Search across 3GPP Release 17–19 specifications including 5G NR, Core Network, Security, and more.
                </p>
              </div>
              <div className="grid gap-2 max-w-xl mx-auto">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => submit(s)}
                    className="text-left text-sm px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-blue-500/40 text-slate-300 transition-all"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="flex-shrink-0 border-t border-slate-800 bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-3 items-end bg-slate-800 border border-slate-700 focus-within:border-blue-500/60 rounded-2xl px-4 py-3 transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about 3GPP specifications..."
              rows={1}
              className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm resize-none outline-none max-h-32 overflow-y-auto"
              style={{ minHeight: "24px" }}
            />
            <button
              onClick={() => submit(input)}
              disabled={!input.trim() || loading}
              className="flex-shrink-0 w-8 h-8 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
            >
              {loading
                ? <Loader2 className="w-4 h-4 text-white animate-spin" />
                : <Send className="w-4 h-4 text-white" />
              }
            </button>
          </div>
          <p className="text-center text-xs text-slate-600 mt-2">
            Answers sourced from 3GPP Rel-17 · Rel-18 · Rel-19 specifications
          </p>
        </div>
      </footer>
    </div>
  );
}
