// src/types/workflow.ts — TypeScript mirror of backend BlogState + SSE event types

export type HITLNodeName =
  | 'hitl_topics'
  | 'hitl_titles'
  | 'hitl_sources'
  | 'hitl_outline'
  | 'hitl_draft'
  | 'hitl_final';

export type HumanAction = 'approve' | 'edit' | 'regenerate';

// Unified payload for all POST /api/workflow/resume calls
export interface HITLResponse {
  human_action: HumanAction;
  human_feedback?: string;          // HITL 3 (DraftEditor) free-text feedback
  selected_strategy?: {             // HITL 4 (FinalApproval) strategy choice
    name: string;
    guidance: string;
    label?: string;
    description?: string;
    icon?: string;
  };
  topic?: TopicItem;                // HITL 1a (TopicSelect)
  title?: TitleItem;                // HITL 1b (TitleSelect)
  accepted_sources?: SourceItem[];  // HITL 1c (SourceReview)
  edited_outline?: OutlineData;     // HITL 2 (OutlineEditor)
  edited_draft?: DraftArticle;      // HITL 3 (DraftEditor) direct edit
}

// ── Domain types (mirror backend BlogState fields) ───────────────

export interface TopicItem {
  title: string;
  description: string;
  trend_signal: string;
}

export interface TitleItem {
  title: string;
  angle: string;
  primary_keyword: string;
  seo_rationale: string;
}

export interface SourceItem {
  id: number;
  title: string;
  url: string;
  publisher: string;
  date: string;
  tier: string;
  snippet: string;
  key_data_point: string;
  grounded?: boolean;
}

export interface OutlineSection {
  heading: string;
  key_points: string[];
  estimated_words: number;
}

export interface OutlineData {
  sections: OutlineSection[];
  comparison: {
    heading: string;
    alternatives: string[];
  };
  anti_recommendation: {
    heading: string;
    focus: string;
  };
  tco_analysis: {
    heading: string;
    cost_categories: string[];
  };
}

export interface ArticleSection {
  heading: string;
  content: string;
  chart_suggestion?: string;
  image_prompt?: string;
}

export interface DraftArticle {
  article_title: string;
  executive_summary: string;
  sections: ArticleSection[];
  comparison?: {
    heading: string;
    alternatives: Array<{
      name: string;
      pros: string;
      cons: string;
      tco_note: string;
      best_for: string;
    }>;
    content?: string;
  };
  anti_recommendation?: { heading: string; content: string };
  tco_analysis?: { heading: string; content: string };
  conclusion?: string;
  references?: string[];
  metadata?: {
    seo_slug: string;
    meta_description: string;
    title_tag: string;
    word_count: number;
  };
  quality_audit?: Array<{ check: string; passed: boolean; note: string }>;
}

export interface QACheck {
  category: string;
  check: string;
  passed: boolean;
  note: string;
}

export interface RerunStrategy {
  icon: string;
  label: string;
  name: string;
  description: string;
  guidance: string;
}

// ── SSE event types ────────────────────────────────────────────────

export interface SSEPhaseStart {
  node: string;
}

export interface SSEProgress {
  node: string;
  data: Record<string, unknown>;
}

export interface SSEHITLWaiting {
  phase: number;
  step: HITLNodeName;
  data: Record<string, unknown>;
  thread_id: string;
}

export interface SSEComplete {
  thread_id: string;
}

export interface SSEError {
  message: string;
  thread_id?: string;
}

export type SSEEventType = 'phase_start' | 'progress' | 'hitl_waiting' | 'complete' | 'error';

// ── Workflow status ───────────────────────────────────────────────

export type WorkflowPhase = 1 | 2 | 3 | 4;

export interface WorkflowStatus {
  threadId: string | null;
  phase: WorkflowPhase;
  currentNode: string | null;
  hitlStep: HITLNodeName | null;
  hitlData: Record<string, unknown> | null;
  isRunning: boolean;
  isComplete: boolean;
  error: string | null;
}
