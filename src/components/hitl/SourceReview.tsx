import { useState } from 'react';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import type { SourceItem } from '../../types/workflow';

interface Props {
  sources: SourceItem[];
  titleText: string;
  onApprove: (accepted: SourceItem[]) => void;
  onRegenerate: () => void;
  disabled?: boolean;
}

export function SourceReview({ sources, titleText, onApprove, onRegenerate, disabled }: Props) {
  const [checked, setChecked] = useState<Set<number>>(
    new Set(sources.map((s) => s.id)),
  );

  function toggle(id: number) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const accepted = sources.filter((s) => checked.has(s.id));

  const tierColor: Record<string, string> = {
    'Tier 1': 'text-violet-400 bg-violet-500/10 border-violet-500/30',
    'Tier 2': 'text-sky-400 bg-sky-500/10 border-sky-500/30',
    'Tier 3': 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    'Tier 4': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  };

  return (
    <PhasePanel
      title="Deep Research Sources"
      subtitle={`8 high-authority sources for: ${titleText}`}
      actions={
        <button
          onClick={onRegenerate}
          disabled={disabled}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-300 transition-all text-sm disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Re-research
        </button>
      }
    >
      <p className="text-sm text-slate-400 -mt-4">
        Toggle sources to include as primary citations. Deselected sources are kept as supplementary context.
      </p>

      <div className="space-y-3">
        {sources.map((src) => {
          const isChecked = checked.has(src.id);
          const tierCls = tierColor[src.tier] ?? 'text-slate-400 bg-slate-800 border-slate-700';
          return (
            <label
              key={src.id}
              className={`flex gap-4 p-5 rounded-2xl border cursor-pointer transition-all ${
                isChecked
                  ? 'border-indigo-500/50 bg-slate-900'
                  : 'border-slate-800 bg-slate-900/50 opacity-60'
              }`}
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => toggle(src.id)}
                disabled={disabled}
                className="mt-1 w-4 h-4 rounded accent-indigo-500 cursor-pointer"
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${tierCls}`}>
                    {src.tier}
                  </span>
                  {src.grounded && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
                      ✓ GROUNDED
                    </span>
                  )}
                  <span className="text-xs text-slate-500">{src.date}</span>
                </div>
                <h4 className="font-semibold text-slate-200 mb-1 leading-snug">{src.title}</h4>
                <p className="text-xs text-slate-500 mb-1">
                  🏛 {src.publisher} &nbsp;·&nbsp;
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-indigo-400 hover:underline"
                  >
                    {src.url.slice(0, 50)}…
                  </a>
                </p>
                <p className="text-sm text-slate-400 leading-relaxed">{src.snippet}</p>
                {src.key_data_point && (
                  <p className="text-xs text-indigo-300 mt-1">📊 {src.key_data_point}</p>
                )}
              </div>
            </label>
          );
        })}
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          {accepted.length} / {sources.length} sources selected as primary
        </p>
        <button
          onClick={() => onApprove(accepted)}
          disabled={accepted.length === 0 || disabled}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Confirm Sources
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </PhasePanel>
  );
}
