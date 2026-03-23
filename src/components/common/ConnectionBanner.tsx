// src/components/common/ConnectionBanner.tsx — Transient SSE reconnection status banner

export type ConnStatus = 'reconnecting' | 'reconnected';

interface ConnectionBannerProps {
  status: ConnStatus;
  attempt?: number;
  maxAttempts?: number;
}

export function ConnectionBanner({ status, attempt, maxAttempts }: ConnectionBannerProps) {
  if (status === 'reconnecting') {
    return (
      <div className="fixed top-16 inset-x-0 z-40 flex justify-center pointer-events-none py-2">
        <div className="flex items-center gap-2 px-4 py-1.5 bg-amber-500/15 border border-amber-500/40 rounded-full text-amber-300 text-sm shadow-lg">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          Reconnecting… (attempt {attempt}/{maxAttempts})
        </div>
      </div>
    );
  }

  return (
    <div className="fixed top-16 inset-x-0 z-40 flex justify-center pointer-events-none py-2">
      <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500/15 border border-emerald-500/40 rounded-full text-emerald-300 text-sm shadow-lg">
        <span className="w-2 h-2 rounded-full bg-emerald-400" />
        Reconnected
      </div>
    </div>
  );
}
