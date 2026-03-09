import { cn } from '@/lib/utils';

interface StateProps {
  className?: string;
}

export function LoadingState({ className }: StateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 border border-border bg-card px-6 py-16 text-muted-foreground', className)}>
      <div className="h-8 w-8 animate-spin border-2 border-foreground/70 border-t-transparent" />
      <p className="font-mono text-xs uppercase tracking-[0.22em]">Loading dataset</p>
    </div>
  );
}

export function EmptyState({ message = 'No items found.', className }: StateProps & { message?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 border border-dashed border-border bg-card px-6 py-16 text-muted-foreground', className)}>
      <svg className="h-10 w-10 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
      </svg>
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function ErrorState({ error, className }: StateProps & { error?: string | null }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 py-16', className)}>
      <div className="max-w-2xl border border-destructive/30 bg-destructive/10 px-4 py-4 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-destructive">Failed to load data</p>
        {error && <p className="mt-2 text-xs text-muted-foreground">{error}</p>}
      </div>
    </div>
  );
}
