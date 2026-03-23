import type { HITLResponse } from '../types/workflow';

const API_BASE = 'http://localhost:3001/api';

/**
 * POST helper —共通エラーハンドリング
 */
async function post<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * ワークフロー開始 — thread_id を取得
 * @param category ユーザーが選択したカテゴリ
 * @returns thread_id
 */
export async function startWorkflow(category: string): Promise<{ thread_id: string }> {
  return post<{ thread_id: string }>('/workflow/start', { category });
}

/**
 * HITL応答を送信し、ワークフロー再開
 * @param thread_id ワークフロー ID
 * @param response HITLチェックポイントでのユーザー応答
 */
export async function resumeWorkflow(thread_id: string, response: HITLResponse): Promise<void> {
  await post<void>('/workflow/resume', { thread_id, ...response });
}

/**
 * ワークフロー状態を取得（ポーリングフォールバック用）
 * @param thread_id ワークフロー ID
 */
export async function getWorkflowState(thread_id: string): Promise<unknown> {
  const res = await fetch(`${API_BASE}/workflow/state/${thread_id}`);
  if (!res.ok) {
    throw new Error(`Failed to get workflow state: ${res.statusText}`);
  }
  return res.json();
}
