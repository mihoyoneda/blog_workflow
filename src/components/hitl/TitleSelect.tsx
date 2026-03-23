import { useState } from 'react';
import { ArrowRight, RefreshCw, Tag } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import { FeedbackInput } from '../common/FeedbackInput';
import type { TitleItem } from '../../types/workflow';

interface Props {
  titles: TitleItem[];
  topicName: string;
  onApprove: (title: TitleItem) => void;
  onRegenerate: (feedback: string) => void;
  disabled?: boolean;
}

export function TitleSelect({ titles, topicName, onApprove, onRegenerate, disabled }: Props) {
  const [selected, setSelected] = useState<TitleItem | null>(null);
  const [feedback, setFeedback] = useState('');

  return (
    <PhasePanel
      title="SEO-Optimised Title Options"
      subtitle={`Refined angles for: ${topicName}`}
    >
      <div className="space-y-4">
        {titles.map((item, i) => (
          <button
            key={i}
            onClick={() => setSelected(item)}
            disabled={disabled}
            className={`w-full text-left p-6 rounded-2xl border transition-all group hover:-translate-y-0.5 ${
              selected?.title === item.title
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-slate-800 bg-slate-900 hover:border-indigo-500/50'
            } disabled:opacity-50`}
          >
            <h3 className="text-xl font-bold mb-3 group-hover:text-purple-400 transition-colors">
              {item.title}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <p className="text-xs font-semibold text-slate-400 mb-1">Editorial Angle</p>
                <p className="text-slate-300">{item.angle}</p>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <p className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1">
                  <Tag className="w-3 h-3" /> Primary Keyword
                </p>
                <p className="text-indigo-400 font-mono">{item.primary_keyword}</p>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <p className="text-xs font-semibold text-slate-400 mb-1">SEO Rationale</p>
                <p className="text-slate-300">{item.seo_rationale}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <FeedbackInput
        value={feedback}
        onChange={setFeedback}
        placeholder='Direction for regeneration (e.g. "More technical, less clickbait")…'
      />

      <div className="flex flex-wrap items-center justify-end gap-3">
        <button
          onClick={() => onRegenerate(feedback)}
          disabled={disabled}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Regenerate
        </button>
        <button
          onClick={() => selected && onApprove(selected)}
          disabled={!selected || disabled}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Confirm Title
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </PhasePanel>
  );
}
