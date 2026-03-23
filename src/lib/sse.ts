// src/lib/sse.ts — EventSource wrapper with typed callbacks and exponential-backoff reconnect

import type {
  SSEComplete,
  SSEError,
  SSEEventType,
  SSEHITLWaiting,
  SSEPhaseStart,
  SSEProgress,
} from '../types/workflow';

const API_BASE = 'http://localhost:3001';
const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

export interface SSEHandlers {
  onPhaseStart?: (data: SSEPhaseStart) => void;
  onProgress?: (data: SSEProgress) => void;
  onHITLWaiting?: (data: SSEHITLWaiting) => void;
  onComplete?: (data: SSEComplete) => void;
  onError?: (data: SSEError) => void;
  /** Called each time a reconnect attempt starts. */
  onReconnecting?: (attempt: number, maxAttempts: number) => void;
  /** Called when the first SSE event arrives after a reconnect. */
  onReconnected?: () => void;
}

export function subscribeWorkflow(threadId: string, handlers: SSEHandlers): () => void {
  const url = `${API_BASE}/api/workflow/stream/${threadId}`;
  let es: EventSource | null = null;
  let retries = 0;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  // Set to true when we close the connection intentionally (terminal event or cleanup).
  let intentionallyClosed = false;
  // Set to true after a retry so we fire onReconnected on the next event.
  let pendingReconnected = false;

  function parseData<T>(raw: string): T {
    try {
      return JSON.parse(raw) as T;
    } catch {
      return {} as T;
    }
  }

  function connect() {
    if (intentionallyClosed) return;

    es = new EventSource(url);

    const eventTypes: SSEEventType[] = [
      'phase_start',
      'progress',
      'hitl_waiting',
      'complete',
      'error',
    ];

    for (const type of eventTypes) {
      es.addEventListener(type, (ev: MessageEvent) => {
        // First event after a retry → notify caller and reset counter.
        if (pendingReconnected) {
          pendingReconnected = false;
          retries = 0;
          handlers.onReconnected?.();
        }

        const data = parseData(ev.data);
        switch (type) {
          case 'phase_start':
            handlers.onPhaseStart?.(data as SSEPhaseStart);
            break;
          case 'progress':
            handlers.onProgress?.(data as SSEProgress);
            break;
          case 'hitl_waiting':
            handlers.onHITLWaiting?.(data as SSEHITLWaiting);
            // Intentional end — stop here, do not retry.
            intentionallyClosed = true;
            es?.close();
            break;
          case 'complete':
            handlers.onComplete?.(data as SSEComplete);
            intentionallyClosed = true;
            es?.close();
            break;
          case 'error':
            handlers.onError?.(data as SSEError);
            intentionallyClosed = true;
            es?.close();
            break;
        }
      });
    }

    es.onerror = () => {
      // Close to prevent EventSource's built-in reconnect from doubling up.
      es?.close();
      es = null;

      if (intentionallyClosed) return;

      if (retries < MAX_RETRIES) {
        retries++;
        // Exponential backoff: 1 s, 2 s, 4 s, 8 s, 16 s
        const delay = BASE_DELAY_MS * Math.pow(2, retries - 1);
        pendingReconnected = true;
        handlers.onReconnecting?.(retries, MAX_RETRIES);
        retryTimer = setTimeout(connect, delay);
      } else {
        handlers.onError?.({
          message: `Connection lost after ${MAX_RETRIES} attempts. Please refresh the page.`,
        });
      }
    };
  }

  connect();

  return () => {
    intentionallyClosed = true;
    if (retryTimer !== null) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    es?.close();
  };
}
