import { useState } from 'react';
import { ArrowRight, RefreshCw, CheckCircle2, Pencil, X } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import { FeedbackInput } from '../common/FeedbackInput';
import { MarkdownPreview } from '../common/MarkdownPreview';
import type { DraftArticle } from '../../types/workflow';

interface Props {
  draft: DraftArticle;
  actualWriter: string;
  fallbackReason: string;
  onApprove: (editedDraft?: DraftArticle) => void;
  onRegenerate: (feedback: string) => void;
  disabled?: boolean;
}

function articleToMarkdown(draft: DraftArticle): string {
  const lines: string[] = [`# ${draft.article_title}\n`];
  lines.push(`> ${draft.executive_summary}\n`);
  for (const sec of draft.sections ?? []) {
    lines.push(`\n## ${sec.heading}\n`);
    lines.push(sec.content ?? '');
    if (sec.chart_suggestion) lines.push(`\n*📊 ${sec.chart_suggestion}*\n`);
  }
  if (draft.comparison?.content) {
    lines.push(`\n## ${draft.comparison.heading ?? 'Comparative Analysis'}\n`);
    lines.push(draft.comparison.content);
  }
  if (draft.tco_analysis?.content) {
    lines.push(`\n## ${draft.tco_analysis.heading ?? 'TCO Analysis'}\n`);
    lines.push(draft.tco_analysis.content);
  }
  if (draft.anti_recommendation?.content) {
    lines.push(`\n## ${draft.anti_recommendation.heading ?? 'When NOT to Use'}\n`);
    lines.push(draft.anti_recommendation.content);
  }
  if (draft.conclusion) {
    lines.push(`\n## Conclusion\n${draft.conclusion}`);
  }
  return lines.join('\n');
}

const inputCls =
  'w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-indigo-500 text-sm';
const textareaCls =
  'w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-indigo-500 resize-none text-sm leading-relaxed';

export function DraftEditor({
  draft,
  actualWriter,
  fallbackReason,
  onApprove,
  onRegenerate,
  disabled,
}: Props) {
  const [feedback, setFeedback] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editedDraft, setEditedDraft] = useState<DraftArticle>(() =>
    JSON.parse(JSON.stringify(draft)),
  );

  const writerLabel =
    actualWriter === 'claude'
      ? 'Claude'
      : actualWriter === 'gemini_fallback'
      ? 'Gemini (fallback)'
      : 'Gemini';

  function cancelEdit() {
    setEditedDraft(JSON.parse(JSON.stringify(draft)));
    setEditMode(false);
  }

  function updateSection(i: number, field: 'heading' | 'content', value: string) {
    setEditedDraft((prev) => {
      const sections = prev.sections.map((s, idx) =>
        idx === i ? { ...s, [field]: value } : s,
      );
      return { ...prev, sections };
    });
  }

  return (
    <PhasePanel
      title="Draft Review"
      subtitle={`Written by ${writerLabel} · ${draft.metadata?.word_count ?? '?'} words`}
    >
      {fallbackReason && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm">
          ⚠️ {fallbackReason}
        </div>
      )}

      {/* Preview or Edit */}
      {editMode ? (
        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          {/* Title */}
          <div>
            <p className="text-xs text-slate-500 mb-1">Article Title</p>
            <input
              value={editedDraft.article_title}
              onChange={(e) =>
                setEditedDraft((prev) => ({ ...prev, article_title: e.target.value }))
              }
              className={inputCls + ' font-semibold'}
            />
          </div>

          {/* Executive summary */}
          <div>
            <p className="text-xs text-slate-500 mb-1">Executive Summary</p>
            <textarea
              value={editedDraft.executive_summary}
              onChange={(e) =>
                setEditedDraft((prev) => ({ ...prev, executive_summary: e.target.value }))
              }
              rows={3}
              className={textareaCls}
            />
          </div>

          {/* Sections */}
          {editedDraft.sections?.map((sec, i) => (
            <div key={i} className="p-4 rounded-xl border border-slate-800 space-y-2">
              <input
                value={sec.heading}
                onChange={(e) => updateSection(i, 'heading', e.target.value)}
                className={inputCls + ' font-semibold'}
                placeholder="Section heading"
              />
              <textarea
                value={sec.content}
                onChange={(e) => updateSection(i, 'content', e.target.value)}
                rows={7}
                className={textareaCls}
              />
            </div>
          ))}

          {/* Conclusion */}
          {editedDraft.conclusion !== undefined && (
            <div>
              <p className="text-xs text-slate-500 mb-1">Conclusion</p>
              <textarea
                value={editedDraft.conclusion}
                onChange={(e) =>
                  setEditedDraft((prev) => ({ ...prev, conclusion: e.target.value }))
                }
                rows={4}
                className={textareaCls}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 max-h-[60vh] overflow-y-auto">
          <MarkdownPreview content={articleToMarkdown(draft)} />
        </div>
      )}

      {/* Metadata */}
      {!editMode && draft.metadata && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <p className="text-xs text-slate-500 mb-1">SEO Slug</p>
            <p className="text-indigo-400 font-mono">/{draft.metadata.seo_slug}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 sm:col-span-2">
            <p className="text-xs text-slate-500 mb-1">Meta Description</p>
            <p className="text-slate-300">{draft.metadata.meta_description}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      {editMode ? (
        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            onClick={cancelEdit}
            disabled={disabled}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-400 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
          >
            <X className="w-4 h-4" />
            Cancel
          </button>
          <button
            onClick={() => onApprove(editedDraft)}
            disabled={disabled}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-40"
          >
            <CheckCircle2 className="w-5 h-5" />
            Save & Approve
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <FeedbackInput value={feedback} onChange={setFeedback} />
          <div className="flex flex-wrap items-center justify-end gap-3">
            <button
              onClick={() => setEditMode(true)}
              disabled={disabled}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
            >
              <Pencil className="w-4 h-4" />
              Edit
            </button>
            <button
              onClick={() => onRegenerate(feedback)}
              disabled={disabled}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4" />
              Regenerate
            </button>
            <button
              onClick={() => onApprove()}
              disabled={disabled}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-40"
            >
              <CheckCircle2 className="w-5 h-5" />
              Approve Draft
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </PhasePanel>
  );
}
