import { FileText } from "lucide-react";
import type { Source } from "@/lib/api";

export function SourceCard({ source, index }: { source: Source; index: number }) {
  const seriesLabel = source.series.replace("_series", " series");
  const score = Math.round(source.score * 100);

  return (
    <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-800 border border-slate-700 hover:border-blue-500/40 transition-colors">
      <div className="mt-0.5 flex-shrink-0">
        <FileText className="w-4 h-4 text-blue-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-200 truncate">
          TS {source.spec_number}
        </p>
        <p className="text-xs text-slate-400 truncate">{source.release} · {seriesLabel}</p>
      </div>
      <span className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">
        {score}%
      </span>
    </div>
  );
}
