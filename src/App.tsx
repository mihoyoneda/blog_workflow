import { useReducer, useEffect, useRef, useCallback, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Sparkles, Loader2, CheckCircle2, RotateCcw } from 'lucide-react';
import { startWorkflow, resumeWorkflow } from './lib/api';
import { subscribeWorkflow } from './lib/sse';
import type { SSEHandlers } from './lib/sse';
import type {
  WorkflowStatus,
  HITLNodeName,
  HITLResponse,
  TopicItem,
  TitleItem,
  SourceItem,
  OutlineData,
  DraftArticle,
  RerunStrategy,
} from './types/workflow';
import { TopicSelect } from './components/hitl/TopicSelect';
import { TitleSelect } from './components/hitl/TitleSelect';
import { SourceReview } from './components/hitl/SourceReview';
import { OutlineEditor } from './components/hitl/OutlineEditor';
import { DraftEditor } from './components/hitl/DraftEditor';
import { FinalApproval } from './components/hitl/FinalApproval';
import { ConnectionBanner } from './components/common/ConnectionBanner';
import { WorkflowProgress } from './components/WorkflowProgress';

// ── Types ────────────────────────────────────────────────────────

type ConnBannerState =
  | { visible: false }
  | { visible: true; status: 'reconnecting'; attempt: number; maxAttempts: number }
  | { visible: true; status: 'reconnected' };

type Action =
  | { type: 'WORKFLOW_STARTED'; threadId: string }
  | { type: 'PHASE_START'; node: string }
  | { type: 'PROGRESS'; node: string }
  | { type: 'HITL_WAITING'; phase: number; step: HITLNodeName; data: Record<string, unknown> }
  | { type: 'HITL_RESUMED' }
  | { type: 'COMPLETE' }
  | { type: 'ERROR'; message: string }
  | { type: 'RESET' };

const INITIAL_STATE: WorkflowStatus = {
  threadId: null,
  phase: 1,
  currentNode: null,
  hitlStep: null,
  hitlData: null,
  isRunning: false,
  isComplete: false,
  error: null,
};

const CATEGORIES = [
  'AI Performance Engineering',
  'GPU Computing & Hardware',
  'High-Performance Networking',
  'Robotics & Edge Computing',
];

// ── Reducer ──────────────────────────────────────────────────────

function reducer(state: WorkflowStatus, action: Action): WorkflowStatus {
  switch (action.type) {
    case 'WORKFLOW_STARTED':
      return { ...state, threadId: action.threadId, isRunning: true, error: null };

    case 'PHASE_START':
      return { ...state, currentNode: action.node, isRunning: true };

    case 'PROGRESS':
      return { ...state, currentNode: action.node, isRunning: true };

    case 'HITL_WAITING':
      return {
        ...state,
        phase: action.phase as 1 | 2 | 3 | 4,
        hitlStep: action.step,
        hitlData: action.data,
        isRunning: false,
      };

    case 'HITL_RESUMED':
      return { ...state, hitlStep: null, hitlData: null, isRunning: true };

    case 'COMPLETE':
      return { ...state, isRunning: false, isComplete: true, hitlStep: null, hitlData: null };

    case 'ERROR':
      return { ...state, isRunning: false, error: action.message };

    case 'RESET':
      return { ...INITIAL_STATE };

    default:
      return state;
  }
}

// ── App Component ────────────────────────────────────────────────

export default function App() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [connBanner, setConnBanner] = useState<ConnBannerState>({ visible: false });
  const sseCleanupRef = useRef<(() => void) | null>(null);

  // ── SSE subscription ─────────────────────────────────────────

  const openSSE = useCallback(
    (threadId: string) => {
      // Cancel any existing subscription
      sseCleanupRef.current?.();
      sseCleanupRef.current = null;

      const handlers: SSEHandlers = {
        onPhaseStart(data) {
          dispatch({ type: 'PHASE_START', node: data.node });
        },
        onProgress(data) {
          dispatch({ type: 'PROGRESS', node: data.node });
        },
        onHITLWaiting(data) {
          dispatch({
            type: 'HITL_WAITING',
            phase: data.phase,
            step: data.step,
            data: data.data,
          });
        },
        onComplete() {
          dispatch({ type: 'COMPLETE' });
        },
        onError(data) {
          dispatch({ type: 'ERROR', message: data.message });
        },
        onReconnecting(attempt, maxAttempts) {
          setConnBanner({
            visible: true,
            status: 'reconnecting',
            attempt,
            maxAttempts,
          });
        },
        onReconnected() {
          setConnBanner({ visible: true, status: 'reconnected' });
          setTimeout(() => setConnBanner({ visible: false }), 3000);
        },
      };

      sseCleanupRef.current = subscribeWorkflow(threadId, handlers);
    },
    []
  );

  // ── Cleanup on unmount ───────────────────────────────────────

  useEffect(() => {
    return () => {
      sseCleanupRef.current?.();
    };
  }, []);

  // ── Event handlers ───────────────────────────────────────────

  const handleCategorySelect = async (category: string) => {
    setSelectedCategory(category);
    try {
      const { thread_id } = await startWorkflow(category);
      dispatch({ type: 'WORKFLOW_STARTED', threadId: thread_id });
      openSSE(thread_id);
    } catch (err) {
      dispatch({ type: 'ERROR', message: (err as Error).message });
    }
  };

  const handleResume = async (response: HITLResponse) => {
    if (!state.threadId) return;
    dispatch({ type: 'HITL_RESUMED' });
    try {
      await resumeWorkflow(state.threadId, response);
      openSSE(state.threadId);
    } catch (err) {
      dispatch({ type: 'ERROR', message: (err as Error).message });
    }
  };

  // ── HITL routing switch ──────────────────────────────────────

  function renderHITL() {
    const { hitlStep, hitlData } = state;
    if (!hitlStep || !hitlData) return null;
    const disabled = state.isRunning;

    switch (hitlStep) {
      case 'hitl_topics': {
        const topics = hitlData.topics as TopicItem[];
        return (
          <TopicSelect
            topics={topics}
            category={selectedCategory}
            disabled={disabled}
            onApprove={(topic) => handleResume({ human_action: 'approve', topic })}
            onRegenerate={(feedback) =>
              handleResume({
                human_action: 'regenerate',
                human_feedback: feedback || undefined,
              })
            }
          />
        );
      }

      case 'hitl_titles': {
        const titles = hitlData.titles as TitleItem[];
        return (
          <TitleSelect
            titles={titles}
            topicName={selectedCategory}
            disabled={disabled}
            onApprove={(title) => handleResume({ human_action: 'approve', title })}
            onRegenerate={(feedback) =>
              handleResume({
                human_action: 'regenerate',
                human_feedback: feedback || undefined,
              })
            }
          />
        );
      }

      case 'hitl_sources': {
        const sources = hitlData.search_results as SourceItem[];
        return (
          <SourceReview
            sources={sources}
            titleText=""
            disabled={disabled}
            onApprove={(accepted) =>
              handleResume({ human_action: 'approve', accepted_sources: accepted })
            }
            onRegenerate={() => handleResume({ human_action: 'regenerate' })}
          />
        );
      }

      case 'hitl_outline': {
        const outline = hitlData.outline as OutlineData;
        return (
          <OutlineEditor
            outline={outline}
            titleText=""
            disabled={disabled}
            onApprove={(editedOutline) =>
              handleResume({ human_action: 'approve', edited_outline: editedOutline })
            }
            onRegenerate={(feedback) =>
              handleResume({
                human_action: 'regenerate',
                human_feedback: feedback || undefined,
              })
            }
          />
        );
      }

      case 'hitl_draft': {
        const draft = hitlData.draft as DraftArticle;
        const actualWriter = (hitlData.actual_writer as string) ?? '';
        const fallbackReason = (hitlData.fallback_reason as string) ?? '';
        return (
          <DraftEditor
            draft={draft}
            actualWriter={actualWriter}
            fallbackReason={fallbackReason}
            disabled={disabled}
            onApprove={(editedDraft) =>
              handleResume({
                human_action: 'approve',
                ...(editedDraft ? { edited_draft: editedDraft } : {}),
              })
            }
            onRegenerate={(feedback) =>
              handleResume({
                human_action: 'regenerate',
                human_feedback: feedback || undefined,
              })
            }
          />
        );
      }

      case 'hitl_final': {
        const draft = hitlData.draft as DraftArticle;
        const qaChecks = (hitlData.qa_checks as any[]) ?? [];
        const rubricScores = (hitlData.rubric_scores as Record<string, number>) ?? null;
        const rerunStrategies = (hitlData.rerun_strategies as RerunStrategy[]) ?? [];
        const heroImageUrl = (hitlData.hero_image_url as string) ?? '';
        return (
          <FinalApproval
            draft={draft}
            qaChecks={qaChecks}
            rubricScores={rubricScores}
            rerunStrategies={rerunStrategies}
            heroImageUrl={heroImageUrl}
            disabled={disabled}
            onApprove={() => handleResume({ human_action: 'approve' })}
            onRegenerate={(strategy, feedback) =>
              handleResume({
                human_action: 'regenerate',
                selected_strategy: strategy ?? undefined,
                human_feedback: feedback || undefined,
              })
            }
          />
        );
      }

      default:
        return null;
    }
  }

  // ── Render ───────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 pb-20">
      {/* Connection banner */}
      {connBanner.visible && (
        <ConnectionBanner
          status={connBanner.status === 'reconnecting' ? 'reconnecting' : 'reconnected'}
          {...('attempt' in connBanner ? { attempt: connBanner.attempt, maxAttempts: connBanner.maxAttempts } : {})}
        />
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-lg">
            <Sparkles className="w-5 h-5" />
            Antigravity Blog Automator
          </div>

          {state.threadId && <WorkflowProgress phase={state.phase} hitlStep={state.hitlStep} isRunning={state.isRunning} />}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 mt-12">
        {/* Global error display */}
        {state.error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400"
          >
            <p className="mb-3">{state.error}</p>
            <button
              onClick={() => dispatch({ type: 'RESET' })}
              className="inline-flex items-center gap-2 text-sm underline hover:text-red-300 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Start over
            </button>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {/* Screen 1: Category selection */}
          {!state.threadId && !state.error && (
            <motion.div
              key="category"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="text-center"
            >
              <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                What Would You Like to Write About?
              </h1>
              <p className="text-slate-400 mb-12">Select a category to begin your AI-assisted article creation.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {CATEGORIES.map((cat) => (
                  <motion.button
                    key={cat}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleCategorySelect(cat)}
                    disabled={state.isRunning}
                    className="p-6 bg-slate-800/50 border border-indigo-500/30 rounded-xl hover:bg-slate-700/50 hover:border-indigo-400/60 transition-all text-left font-semibold text-indigo-300"
                  >
                    {cat}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Screen 2: Running (no HITL step pending) */}
          {state.threadId && state.isRunning && !state.hitlStep && (
            <motion.div
              key="running"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <Loader2 className="w-12 h-12 text-indigo-400 animate-spin mb-4" />
              <p className="text-slate-300">Processing: {state.currentNode ?? 'workflow'}…</p>
            </motion.div>
          )}

          {/* Screen 3: HITL checkpoint */}
          {state.threadId && state.hitlStep && (
            <motion.div
              key={state.hitlStep}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderHITL()}
            </motion.div>
          )}

          {/* Screen 4: Complete */}
          {state.isComplete && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="text-center py-20"
            >
              <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-3xl font-bold mb-4">Article Published Successfully! 🎉</h2>
              <p className="text-slate-400 mb-8">Your article has been generated and is ready for review.</p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => dispatch({ type: 'RESET' })}
                className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-semibold transition-colors"
              >
                Create New Article
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
