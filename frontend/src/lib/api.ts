// Production: NEXT_PUBLIC_API_URL="" → relative paths (/api/chat/stream)
// Local dev: NEXT_PUBLIC_API_URL unset (undefined) → falls back to localhost
// Must use ?? not || because empty string is falsy but valid
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Source {
  spec_name: string;
  spec_number: string;
  release: string;
  series: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  sub_queries: string[];
}

export interface StreamEvent {
  type: "token" | "done";
  content?: string;
  sources?: Source[];
  sub_queries?: string[];
}

export async function* streamChat(
  question: string,
  onSources?: (sources: Source[], subQueries: string[]) => void
): AsyncGenerator<string> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const event: StreamEvent = JSON.parse(line.slice(6));
        if (event.type === "token" && event.content) {
          yield event.content;
        } else if (event.type === "done") {
          onSources?.(event.sources ?? [], event.sub_queries ?? []);
        }
      } catch {}
    }
  }
}

export async function healthCheck(): Promise<{ status: string; chunks_indexed: number }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
