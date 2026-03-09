import { ReviewStatus, SubmissionStatus } from '@/lib/api';
import { cn } from '@/lib/utils';

const reviewStyles: Record<ReviewStatus, string> = {
  pending: 'border-amber-300 bg-amber-50 text-amber-700',
  approved: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  rejected: 'border-red-300 bg-red-50 text-red-700',
  needs_revision: 'border-blue-300 bg-blue-50 text-blue-700',
};

const reviewDots: Record<ReviewStatus, string> = {
  pending: 'bg-amber-500',
  approved: 'bg-emerald-500',
  rejected: 'bg-red-500',
  needs_revision: 'bg-blue-500',
};

const submissionStyles: Record<SubmissionStatus, string> = {
  queued: 'border-zinc-300 bg-zinc-50 text-zinc-600',
  running: 'border-blue-300 bg-blue-50 text-blue-700',
  completed: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  failed: 'border-red-300 bg-red-50 text-red-700',
};

const submissionDots: Record<SubmissionStatus, string> = {
  queued: 'bg-zinc-400',
  running: 'bg-blue-500',
  completed: 'bg-emerald-500',
  failed: 'bg-red-500',
};

function labelize(value: string): string {
  return value.replaceAll('_', ' ');
}

export function ReviewStatusBadge({ status }: { status?: ReviewStatus | string | null }) {
  const value = ((status ?? 'pending') as ReviewStatus);
  return (
    <span className={cn('status-badge', reviewStyles[value] ?? reviewStyles.pending)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', reviewDots[value] ?? reviewDots.pending)} />
      {labelize(value)}
    </span>
  );
}

export function SubmissionStatusBadge({ status }: { status?: SubmissionStatus | string | null }) {
  const value = ((status ?? 'queued') as SubmissionStatus);
  return (
    <span className={cn('status-badge', submissionStyles[value] ?? submissionStyles.queued)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', submissionDots[value] ?? submissionDots.queued)} />
      {labelize(value)}
    </span>
  );
}

export function ConfidenceScore({ score }: { score?: number | null }) {
  if (score == null) {
    return <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">n/a</span>;
  }

  const percent = Math.round(score * 100);
  const color =
    score >= 0.85
      ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
      : score >= 0.6
        ? 'border-amber-300 bg-amber-50 text-amber-700'
        : 'border-red-300 bg-red-50 text-red-700';

  return (
    <span
      className={cn(
        'inline-flex min-w-[4.5rem] items-center justify-center border px-2 py-1 font-mono text-[11px] tracking-[0.18em]',
        color,
      )}
    >
      {percent}%
    </span>
  );
}
