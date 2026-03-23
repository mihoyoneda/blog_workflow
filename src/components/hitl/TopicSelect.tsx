import { useState } from 'react';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import { FeedbackInput } from '../common/FeedbackInput';
import type { TopicItem } from '../../types/workflow';

interface Props {
  topics: TopicItem[];
  category: string;
  onApprove: (topic: TopicItem) => void;
  onRegenerate: (feedback: string) => void;
  disabled?: boolean;
}

export function TopicSelect({ topics, category, onApprove, onRegenerate, disabled }: Props) {
  const [selected, setSelected] = useState<TopicItem | null>(null);
  const [feedback, setFeedback] = useState('');

  return (
    <PhasePanel
      title="Trending Topics"
      subtitle={`Based on 2025–2026 data in ${category}`}
    >
      <div className="space-y-4">
        {topics.map((topic, i) => (
          <button
            key={i}
            onClick={() => setSelected(topic)}
            disabled={disabled}
            className={`w-full text-left p-6 rounded-2xl border transition-all group hover:-translate-y-0.5 ${
              selected?.title === topic.title
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-slate-800 bg-slate-900 hover:border-indigo-500/50'
            } disabled:opacity-50`}
          >
            <div className="flex gap-6">
              <div className="flex-1 space-y-2">
                <h3 className="text-xl font-bold group-hover:text-indigo-400 transition-colors">
                  {topic.title}
                </h3>
                <p className="text-slate-400 leading-relaxed">{topic.description}</p>
                {topic.trend_signal && (
                  <p className="text-xs text-indigo-400 bg-indigo-500/10 inline-block px-2 py-0.5 rounded-full">
                    📈 {topic.trend_signal}
                  </p>
                )}
              </div>
              <div className="hidden sm:flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                    selected?.title === topic.title
                      ? 'bg-indigo-500'
                      : 'bg-slate-800 group-hover:bg-indigo-500'
                  }`}
                >
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <FeedbackInput
        value={feedback}
        onChange={setFeedback}
        placeholder='Direction for regeneration (e.g. "Focus on enterprise adoption cases")…'
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
          Confirm Topic
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </PhasePanel>
  );
}
