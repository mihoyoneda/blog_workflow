import { useState } from 'react';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import { FeedbackInput } from '../common/FeedbackInput';
import type { OutlineData } from '../../types/workflow';

interface Props {
  outline: OutlineData;
  titleText: string;
  onApprove: (outline: OutlineData) => void;
  onRegenerate: (feedback: string) => void;
  disabled?: boolean;
}

export function OutlineEditor({ outline, titleText, onApprove, onRegenerate, disabled }: Props) {
  const [edited, setEdited] = useState<OutlineData>(outline);
  const [feedback, setFeedback] = useState('');

  function updateSectionHeading(idx: number, value: string) {
    setEdited((prev) => {
      const sections = prev.sections.map((s, i) =>
        i === idx ? { ...s, heading: value } : s,
      );
      return { ...prev, sections };
    });
  }

  function updateKeyPoint(sectionIdx: number, pointIdx: number, value: string) {
    setEdited((prev) => {
      const sections = prev.sections.map((s, si) => {
        if (si !== sectionIdx) return s;
        const key_points = s.key_points.map((p, pi) => (pi === pointIdx ? value : p));
        return { ...s, key_points };
      });
      return { ...prev, sections };
    });
  }

  return (
    <PhasePanel
      title="Article Outline"
      subtitle={`Review and edit the structure for: ${titleText}`}
    >
      <div className="space-y-4">
        {edited.sections.map((section, si) => (
          <div key={si} className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
                Section {si + 1} · ~{section.estimated_words}w
              </span>
            </div>
            <input
              value={section.heading}
              onChange={(e) => updateSectionHeading(si, e.target.value)}
              disabled={disabled}
              className="w-full text-lg font-bold bg-transparent border-b border-slate-700 focus:border-indigo-500 outline-none pb-2 mb-3 text-slate-100"
            />
            <ul className="space-y-2">
              {section.key_points.map((point, pi) => (
                <li key={pi} className="flex items-start gap-2">
                  <span className="text-indigo-400 mt-1.5 text-xs">▸</span>
                  <input
                    value={point}
                    onChange={(e) => updateKeyPoint(si, pi, e.target.value)}
                    disabled={disabled}
                    className="flex-1 bg-transparent border-b border-slate-800 focus:border-indigo-500/50 outline-none text-sm text-slate-300 pb-1"
                  />
                </li>
              ))}
            </ul>
          </div>
        ))}

        {/* Comparison / Anti-rec / TCO summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <p className="text-xs font-semibold text-slate-400 mb-1">Comparison</p>
            <p className="text-sm font-medium text-slate-200">{edited.comparison.heading}</p>
            <ul className="mt-2 space-y-0.5">
              {edited.comparison.alternatives.map((alt, i) => (
                <li key={i} className="text-xs text-slate-400">• {alt}</li>
              ))}
            </ul>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <p className="text-xs font-semibold text-slate-400 mb-1">Anti-Recommendation</p>
            <p className="text-sm font-medium text-slate-200">{edited.anti_recommendation.heading}</p>
            <p className="text-xs text-slate-400 mt-1">{edited.anti_recommendation.focus}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <p className="text-xs font-semibold text-slate-400 mb-1">TCO Analysis</p>
            <p className="text-sm font-medium text-slate-200">{edited.tco_analysis.heading}</p>
            <ul className="mt-2 space-y-0.5">
              {edited.tco_analysis.cost_categories.map((cat, i) => (
                <li key={i} className="text-xs text-slate-400">• {cat}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <FeedbackInput
        value={feedback}
        onChange={setFeedback}
        placeholder='Direction for regeneration (e.g. "Add a cost comparison section, remove the TCO section")…'
      />

      <div className="flex flex-wrap items-center justify-end gap-3">
        <button
          onClick={() => onRegenerate(feedback)}
          disabled={disabled}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Regenerate Outline
        </button>
        <button
          onClick={() => onApprove(edited)}
          disabled={disabled}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-40"
        >
          Approve Outline & Generate Draft
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </PhasePanel>
  );
}
