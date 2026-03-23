import { useState } from 'react';
import { CheckCircle2, ClipboardCheck, Copy, Download, RefreshCw, XCircle } from 'lucide-react';
import { PhasePanel } from '../PhasePanel';
import { FeedbackInput } from '../common/FeedbackInput';
import type { DraftArticle, QACheck, RerunStrategy } from '../../types/workflow';

function draftToMarkdown(draft: DraftArticle): string {
  const lines: string[] = [];

  if (draft.metadata) {
    lines.push('---');
    lines.push(`title: "${draft.metadata.title_tag}"`);
    lines.push(`slug: ${draft.metadata.seo_slug}`);
    lines.push(`description: "${draft.metadata.meta_description}"`);
    lines.push(`word_count: ${draft.metadata.word_count}`);
    lines.push('---', '');
  }

  lines.push(`# ${draft.article_title}`, '');
  lines.push(`## Executive Summary`, '', draft.executive_summary, '');

  for (const section of draft.sections) {
    lines.push(`## ${section.heading}`, '', section.content, '');
  }

  if (draft.comparison) {
    lines.push(`## ${draft.comparison.heading}`, '');
    if (draft.comparison.content) {
      lines.push(draft.comparison.content, '');
    } else {
      for (const alt of draft.comparison.alternatives ?? []) {
        lines.push(`### ${alt.name}`);
        lines.push(`- **Pros:** ${alt.pros}`);
        lines.push(`- **Cons:** ${alt.cons}`);
        lines.push(`- **TCO Note:** ${alt.tco_note}`);
        lines.push(`- **Best For:** ${alt.best_for}`, '');
      }
    }
  }

  if (draft.anti_recommendation) {
    lines.push(`## ${draft.anti_recommendation.heading}`, '', draft.anti_recommendation.content, '');
  }

  if (draft.tco_analysis) {
    lines.push(`## ${draft.tco_analysis.heading}`, '', draft.tco_analysis.content, '');
  }

  if (draft.conclusion) {
    lines.push(`## Conclusion`, '', draft.conclusion, '');
  }

  if (draft.references && draft.references.length > 0) {
    lines.push(`## References`, '');
    draft.references.forEach((ref, i) => lines.push(`${i + 1}. ${ref}`));
    lines.push('');
  }

  return lines.join('\n');
}

interface Props {
  draft: DraftArticle;
  qaChecks: QACheck[];
  rubricScores: Record<string, number> | null;
  rerunStrategies: RerunStrategy[];
  heroImageUrl: string;
  onApprove: () => void;
  onRegenerate: (strategy: RerunStrategy | null, feedback: string) => void;
  disabled?: boolean;
}

export function FinalApproval({
  draft,
  qaChecks,
  rubricScores,
  rerunStrategies,
  heroImageUrl,
  onApprove,
  onRegenerate,
  disabled,
}: Props) {
  const [selectedStrategy, setSelectedStrategy] = useState<RerunStrategy | null>(null);
  const [feedback, setFeedback] = useState('');
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(draftToMarkdown(draft)).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleDownload() {
    const slug = draft.metadata?.seo_slug
      ?? draft.article_title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const blob = new Blob([draftToMarkdown(draft)], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slug}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const passed = qaChecks.filter((c) => c.passed).length;
  const total = qaChecks.length;
  const pct = total > 0 ? Math.round((passed / total) * 100) : 0;
  const grade = pct >= 90 ? 'A' : pct >= 70 ? 'B' : 'C';
  const gradeColor =
    grade === 'A' ? 'text-emerald-400' : grade === 'B' ? 'text-amber-400' : 'text-red-400';

  const categories: Record<string, QACheck[]> = {};
  for (const check of qaChecks) {
    const cat = check.category ?? 'Other';
    categories[cat] ??= [];
    categories[cat].push(check);
  }

  const canRegenerate = !!selectedStrategy || feedback.trim().length > 0;

  return (
    <PhasePanel
      title="Publication QA"
      subtitle={`${draft.article_title}`}
    >
      {/* Hero image */}
      {heroImageUrl && (
        <img
          src={heroImageUrl}
          alt="Hero"
          className="w-full h-48 object-cover rounded-2xl border border-slate-800"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      )}

      {/* QA score */}
      <div className="flex items-center gap-6 p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <div className={`text-5xl font-black ${gradeColor}`}>{grade}</div>
        <div className="flex-1">
          <div className="flex items-baseline gap-2 mb-1">
            <span className={`text-xl font-bold ${gradeColor}`}>{pct}%</span>
            <span className="text-slate-400 text-sm">{passed}/{total} checks passed</span>
          </div>
          <div className="h-2 rounded-full bg-slate-800">
            <div
              className={`h-full rounded-full transition-all ${
                grade === 'A' ? 'bg-emerald-500' : grade === 'B' ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </div>

      {/* QA checks by category */}
      <div className="space-y-3">
        {Object.entries(categories).map(([cat, checks]) => (
          <div key={cat} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <h4 className="text-sm font-semibold text-slate-300 mb-2">{cat}</h4>
            <div className="space-y-1.5">
              {checks.map((check, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  {check.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                  )}
                  <div>
                    <span className={check.passed ? 'text-slate-300' : 'text-slate-200 font-medium'}>
                      {check.check}
                    </span>
                    {check.note && (
                      <span className="text-slate-500 ml-2 text-xs">— {check.note}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Rubric scores */}
      {rubricScores && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h4 className="text-sm font-semibold text-slate-300 mb-3">Rubric Scores</h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(rubricScores).map(([criterion, score]) => (
              <div key={criterion} className="text-sm">
                <div className="flex justify-between mb-1">
                  <span className="text-slate-400 text-xs">{criterion}</span>
                  <span className={`font-bold text-xs ${score >= 7 ? 'text-emerald-400' : score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                    {score.toFixed(1)}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full ${score >= 7 ? 'bg-emerald-500' : score >= 5 ? 'bg-amber-500' : 'bg-red-500'}`}
                    style={{ width: `${(score / 10) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Regeneration strategies */}
      {rerunStrategies.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300">Regeneration Strategies</h4>
          {rerunStrategies.map((strategy, i) => (
            <button
              key={i}
              onClick={() =>
                setSelectedStrategy((prev) =>
                  prev?.name === strategy.name ? null : strategy,
                )
              }
              disabled={disabled}
              className={`w-full text-left p-4 rounded-xl border transition-all ${
                selectedStrategy?.name === strategy.name
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-slate-800 bg-slate-900 hover:border-slate-600'
              } disabled:opacity-50`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span>{strategy.icon}</span>
                <span className="font-semibold text-sm text-slate-200">{strategy.label}</span>
              </div>
              <p className="text-xs text-slate-400">{strategy.description}</p>
            </button>
          ))}
        </div>
      )}

      {/* Feedback for regeneration */}
      <FeedbackInput
        value={feedback}
        onChange={setFeedback}
        placeholder='Additional direction on top of strategy (e.g. "Especially strengthen the citation in the TCO section")…'
      />

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Export buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            title="Copy as Markdown"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200 transition-all text-sm"
          >
            {copied ? <ClipboardCheck className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy MD'}
          </button>
          <button
            onClick={handleDownload}
            title="Download as .md file"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200 transition-all text-sm"
          >
            <Download className="w-4 h-4" />
            Download .md
          </button>
        </div>

        {/* Workflow actions */}
        <div className="flex items-center gap-3">
          {canRegenerate && (
            <button
              onClick={() => onRegenerate(selectedStrategy, feedback)}
              disabled={disabled}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:border-slate-500 transition-all text-sm disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4" />
              {selectedStrategy ? `Regenerate: ${selectedStrategy.label}` : 'Regenerate with Feedback'}
            </button>
          )}
          <button
            onClick={onApprove}
            disabled={disabled}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-40"
          >
            <CheckCircle2 className="w-5 h-5" />
            Publish Article
          </button>
        </div>
      </div>
    </PhasePanel>
  );
}
