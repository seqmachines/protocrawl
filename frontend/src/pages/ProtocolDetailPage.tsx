import { useEffect, useState, type ComponentType, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  AlignLeft,
  ArrowLeft,
  ClipboardList,
  Database,
  ExternalLink,
  Link2,
  Package2,
  Quote,
  Workflow,
} from 'lucide-react';

import { ErrorState, LoadingState } from '@/components/States';
import { ConfidenceScore, ReviewStatusBadge } from '@/components/StatusBadge';
import { LibraryStructureSection } from '@/components/LibraryStructure';
import { Adapter, api, Barcode, Citation, ProtocolDetail } from '@/lib/api';

type ResourceState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

function createIdleState<T>(): ResourceState<T> {
  return { data: null, loading: true, error: null };
}

function SectionTitle({
  icon,
  label,
  aside,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  aside?: ReactNode;
}) {
  const Icon = icon;
  return (
    <div className="mb-4 flex items-center justify-between gap-3 border-b border-border pb-3">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center border border-border bg-background">
          <Icon className="h-4 w-4" />
        </span>
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-muted-foreground">Section</p>
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">{label}</h2>
        </div>
      </div>
      {aside}
    </div>
  );
}

function SummaryField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value?: ReactNode;
  mono?: boolean;
}) {
  if (value == null || value === '') {
    return null;
  }

  return (
    <div className="border border-border bg-background p-3">
      <dt className="data-label mb-2">{label}</dt>
      <dd className={mono ? 'font-mono text-xs text-foreground' : 'text-sm text-foreground'}>{value}</dd>
    </div>
  );
}

function formatCitation(citation: Citation): string {
  const authors = citation.authors?.length ? citation.authors.join(', ') : null;
  const year = citation.year ? `(${citation.year})` : null;
  return [authors, year, citation.title].filter(Boolean).join(' ');
}

function SummarySection({ protocol }: { protocol: ProtocolDetail }) {
  return (
    <section className="section-card">
      <SectionTitle icon={Database} label="Summary" />
      <dl className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <SummaryField label="Slug" value={protocol.slug} mono />
        <SummaryField label="Version" value={protocol.version} mono />
        <SummaryField label="Assay family" value={protocol.assay_family ? <span className="stat-pill">{protocol.assay_family}</span> : undefined} />
        <SummaryField label="Molecule type" value={protocol.molecule_type} />
        <SummaryField label="Vendor" value={protocol.vendor} />
        <SummaryField label="Platform" value={protocol.platform} />
        <SummaryField label="Confidence" value={<ConfidenceScore score={protocol.confidence_score} />} />
        <SummaryField label="Review status" value={<ReviewStatusBadge status={protocol.review_status} />} />
      </dl>

      {protocol.description && (
        <div className="mt-4 border border-border bg-background p-4">
          <p className="data-label mb-2">Description</p>
          <p className="text-sm text-muted-foreground">{protocol.description}</p>
        </div>
      )}

      {protocol.extraction_notes && (
        <div className="mt-3 border border-border bg-background p-4">
          <p className="data-label mb-2">Extraction notes</p>
          <p className="text-sm text-muted-foreground">{protocol.extraction_notes}</p>
        </div>
      )}
    </section>
  );
}

function BarcodeTable({ barcodes }: { barcodes: Barcode[] }) {
  if (!barcodes.length) {
    return null;
  }

  return (
    <section className="section-card">
      <SectionTitle icon={Workflow} label={`Barcodes (${barcodes.length})`} />
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead className="bg-background/70">
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Role</th>
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Length</th>
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Whitelist</th>
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Addition method</th>
            </tr>
          </thead>
          <tbody>
            {barcodes.map((barcode, index) => (
              <tr key={`${barcode.role}-${barcode.length}-${index}`} className="border-b border-border/70 last:border-0">
                <td className="px-4 py-3">
                  <span className="stat-pill">{barcode.role}</span>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{barcode.length}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  {barcode.whitelist_source ? (
                    <a
                      href={barcode.whitelist_source}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-foreground hover:text-muted-foreground"
                    >
                      {barcode.whitelist_source}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{barcode.addition_method ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function AdapterTable({ adapters }: { adapters: Adapter[] }) {
  if (!adapters.length) {
    return null;
  }

  return (
    <section className="section-card">
      <SectionTitle icon={Link2} label={`Adapters (${adapters.length})`} />
      <div className="overflow-x-auto border border-border">
        <table className="w-full text-sm">
          <thead className="bg-background/70">
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Name</th>
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Position</th>
              <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Sequence</th>
            </tr>
          </thead>
          <tbody>
            {adapters.map((adapter, index) => (
              <tr key={`${adapter.name}-${index}`} className="border-b border-border/70 last:border-0">
                <td className="px-4 py-3">{adapter.name}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{adapter.position}</td>
                <td className="px-4 py-3 font-mono text-xs">{adapter.sequence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CitationsSection({ citations }: { citations: Citation[] }) {
  if (!citations.length) {
    return null;
  }

  return (
    <section className="section-card">
      <SectionTitle icon={Quote} label={`Citations (${citations.length})`} />
      <div className="space-y-3">
        {citations.map((citation, index) => (
          <article key={`${citation.title}-${index}`} className="border border-border bg-background p-4">
            <p className="text-sm">{formatCitation(citation)}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
              {citation.doi && <span className="stat-pill">doi {citation.doi}</span>}
              {citation.pmid && <span className="stat-pill">pmid {citation.pmid}</span>}
              {citation.arxiv_id && <span className="stat-pill">arxiv {citation.arxiv_id}</span>}
              {citation.url && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground"
                >
                  source
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function SupportSection({ protocol }: { protocol: ProtocolDetail }) {
  const hasSteps = protocol.protocol_steps.length > 0;
  const hasKits = protocol.reagent_kits.length > 0;
  const hasSources = protocol.source_urls.length > 0;
  const hasCaveats = protocol.caveats.length > 0;
  const hasQc = protocol.qc_expectations.length > 0;
  const hasFailureModes = protocol.failure_modes.length > 0;

  if (!hasSteps && !hasKits && !hasSources && !hasCaveats && !hasQc && !hasFailureModes) {
    return null;
  }

  return (
    <section className="grid gap-4 xl:grid-cols-2">
      {hasSteps && (
        <div className="section-card">
          <SectionTitle icon={ClipboardList} label="Protocol steps" />
          <ol className="space-y-2">
            {protocol.protocol_steps.map((step, index) => (
              <li key={`${step}-${index}`} className="flex gap-3 border border-border bg-background p-3">
                <span className="font-mono text-xs text-muted-foreground">{String(index + 1).padStart(2, '0')}</span>
                <p className="text-sm text-muted-foreground">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      )}

      {hasKits && (
        <div className="section-card">
          <SectionTitle icon={Package2} label="Reagent kits" />
          <div className="space-y-3">
            {protocol.reagent_kits.map((kit, index) => (
              <div key={`${kit.name}-${index}`} className="border border-border bg-background p-3">
                <p className="font-medium">{kit.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">{kit.vendor}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {kit.catalog_number && <span className="stat-pill">catalog {kit.catalog_number}</span>}
                  {kit.version && <span className="stat-pill">version {kit.version}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasQc && (
        <div className="section-card">
          <SectionTitle icon={AlignLeft} label="QC expectations" />
          <div className="space-y-3">
            {protocol.qc_expectations.map((expectation, index) => (
              <div key={`${expectation.metric}-${index}`} className="border border-border bg-background p-3">
                <p className="font-medium">{expectation.metric}</p>
                <p className="mt-2 font-mono text-xs text-muted-foreground">
                  {expectation.typical_range_low ?? 'n/a'} - {expectation.typical_range_high ?? 'n/a'}
                </p>
                {expectation.notes && <p className="mt-2 text-xs text-muted-foreground">{expectation.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {hasFailureModes && (
        <div className="section-card">
          <SectionTitle icon={Workflow} label="Failure modes" />
          <div className="space-y-3">
            {protocol.failure_modes.map((mode, index) => (
              <div key={`${mode.description}-${index}`} className="border border-border bg-background p-3">
                <p className="font-medium">{mode.description}</p>
                <p className="mt-2 text-xs text-muted-foreground">Symptom: {mode.symptom}</p>
                <p className="mt-1 text-xs text-muted-foreground">Cause: {mode.likely_cause}</p>
                {mode.mitigation && <p className="mt-1 text-xs text-muted-foreground">Mitigation: {mode.mitigation}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {hasSources && (
        <div className="section-card">
          <SectionTitle icon={Link2} label="Source URLs" />
          <div className="space-y-2">
            {protocol.source_urls.map((url) => (
              <a
                key={url}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-3 border border-border bg-background px-3 py-3 text-xs text-muted-foreground hover:text-foreground"
              >
                <span className="break-all font-mono">{url}</span>
                <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
            ))}
          </div>
        </div>
      )}

      {hasCaveats && (
        <div className="section-card">
          <SectionTitle icon={AlignLeft} label="Caveats" />
          <ul className="space-y-2">
            {protocol.caveats.map((caveat, index) => (
              <li key={`${caveat}-${index}`} className="border border-border bg-background p-3 text-sm text-muted-foreground">
                {caveat}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

export default function ProtocolDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [protocol, setProtocol] = useState<ResourceState<ProtocolDetail>>(createIdleState());

  useEffect(() => {
    if (!slug) {
      return;
    }

    setProtocol(createIdleState());

    api.protocols
      .get(slug)
      .then((data) => setProtocol({ data, loading: false, error: null }))
      .catch((error: Error) => setProtocol({ data: null, loading: false, error: error.message }));
  }, [slug]);

  return (
    <div>
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to protocols
      </Link>

      {protocol.loading && <LoadingState />}
      {!protocol.loading && protocol.error && <ErrorState error={protocol.error} />}

      {!protocol.loading && protocol.data && (
        <div className="space-y-4">
          <div className="page-header border-b border-border pb-5">
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted-foreground">Protocol detail</p>
            <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
              <div>
                <h1 className="text-3xl font-semibold tracking-[0.04em]">{protocol.data.name}</h1>
                <p className="mt-2 font-mono text-xs text-muted-foreground">{protocol.data.slug}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {protocol.data.assay_family && <span className="stat-pill">{protocol.data.assay_family}</span>}
                {protocol.data.molecule_type && <span className="stat-pill">{protocol.data.molecule_type}</span>}
                <ReviewStatusBadge status={protocol.data.review_status} />
                <ConfidenceScore score={protocol.data.confidence_score} />
              </div>
            </div>
          </div>

          <SummarySection protocol={protocol.data} />

          {protocol.data.library_structure?.length ? (
            <LibraryStructureSection regions={protocol.data.library_structure} />
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <BarcodeTable barcodes={protocol.data.barcodes} />
            <AdapterTable adapters={protocol.data.adapters} />
          </div>

          <CitationsSection citations={protocol.data.citations} />
          <SupportSection protocol={protocol.data} />
        </div>
      )}
    </div>
  );
}
