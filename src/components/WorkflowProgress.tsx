import { CheckCircle2 } from 'lucide-react';
import type { HITLNodeName, WorkflowPhase } from '../types/workflow';

interface Props {
  phase: WorkflowPhase;
  hitlStep: HITLNodeName | null;
  isRunning: boolean;
}

const PHASES = [
  { num: 1 as WorkflowPhase, label: 'Research', substeps: ['1a', '1b', '1c'] },
  { num: 2 as WorkflowPhase, label: 'Outline', substeps: [] },
  { num: 3 as WorkflowPhase, label: 'Draft', substeps: [] },
  { num: 4 as WorkflowPhase, label: 'QA & Publish', substeps: [] },
];

const SUBSTEP_LABELS: Record<string, string> = {
  hitl_topics: '1a',
  hitl_titles: '1b',
  hitl_sources: '1c',
};

export function WorkflowProgress({ phase, hitlStep, isRunning }: Props) {
  const activeSubstep = hitlStep ? SUBSTEP_LABELS[hitlStep] : null;

  return (
    <div className="flex items-center gap-1 text-sm font-medium">
      {PHASES.map((p, idx) => {
        const isDone = p.num < phase;
        const isActive = p.num === phase;

        return (
          <div key={p.num} className="flex items-center gap-1">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all ${
                isDone
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : isActive
                  ? 'bg-indigo-500/20 text-indigo-300 ring-1 ring-indigo-500/50'
                  : 'text-slate-500'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <span
                  className={`w-2 h-2 rounded-full ${
                    isActive && isRunning ? 'animate-pulse bg-indigo-400' : 'bg-current opacity-50'
                  }`}
                />
              )}
              <span>
                Phase {p.num}: {p.label}
              </span>
              {/* Phase 1 substep indicators */}
              {isActive && p.substeps.length > 0 && (
                <div className="flex items-center gap-0.5 ml-1">
                  {p.substeps.map((sub) => (
                    <span
                      key={sub}
                      className={`text-xs px-1 rounded ${
                        activeSubstep === sub
                          ? 'bg-indigo-500 text-white'
                          : 'bg-slate-700 text-slate-400'
                      }`}
                    >
                      {sub}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {idx < PHASES.length - 1 && (
              <span className="text-slate-700">›</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
