import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Filter, Search, Waypoints } from 'lucide-react';

import { ErrorState, EmptyState, LoadingState } from '@/components/States';
import { ConfidenceScore, ReviewStatusBadge } from '@/components/StatusBadge';
import { api, ProtocolListItem } from '@/lib/api';

export default function ProtocolsPage() {
  const navigate = useNavigate();
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [familyFilter, setFamilyFilter] = useState('');

  useEffect(() => {
    api.protocols
      .list()
      .then(setProtocols)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const families = useMemo(
    () =>
      Array.from(
        new Set(protocols.map((protocol) => protocol.assay_family).filter((value): value is string => Boolean(value))),
      ).sort(),
    [protocols],
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return protocols.filter((protocol) => {
      const haystack = [protocol.name, protocol.slug, protocol.vendor, protocol.description]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      const matchesSearch = !query || haystack.includes(query);
      const matchesFamily = !familyFilter || protocol.assay_family === familyFilter;
      return matchesSearch && matchesFamily;
    });
  }, [protocols, search, familyFilter]);

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center border border-border bg-card">
            <Waypoints className="h-5 w-5" />
          </span>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
              Protocol registry
            </p>
            <h1 className="text-2xl font-semibold tracking-[0.04em]">Browse protocols</h1>
          </div>
          {!loading && !error && <span className="stat-pill">{protocols.length} loaded</span>}
        </div>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Search the local protocol database, inspect library structures, and browse detail records.
        </p>
      </div>

      <section className="section-card mb-5">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_260px]">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by protocol name, slug, vendor, or description"
              className="h-11 w-full border border-border bg-background pl-10 pr-3 text-sm outline-none transition-colors focus:border-foreground/50"
            />
          </label>

          <label className="relative block">
            <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <select
              value={familyFilter}
              onChange={(event) => setFamilyFilter(event.target.value)}
              className="h-11 w-full appearance-none border border-border bg-background pl-10 pr-3 text-sm outline-none transition-colors focus:border-foreground/50"
            >
              <option value="">All assay families</option>
              {families.map((family) => (
                <option key={family} value={family}>
                  {family}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {loading && <LoadingState />}
      {error && <ErrorState error={error} />}
      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          message={search || familyFilter ? 'No protocols match the current filters.' : 'No protocols found.'}
        />
      )}

      {!loading && !error && filtered.length > 0 && (
        <>
          <section className="hidden overflow-hidden border border-border bg-card md:block">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-background/70">
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Name</th>
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Slug</th>
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Assay</th>
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Molecule</th>
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Confidence</th>
                  <th className="px-4 py-3 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Review</th>
                  <th className="w-8 px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {filtered.map((protocol) => (
                  <tr
                    key={protocol.slug}
                    className="table-row-hover border-b border-border/70 last:border-0"
                    onClick={() => navigate(`/protocols/${protocol.slug}`)}
                  >
                    <td className="px-4 py-4 align-top">
                      <div className="space-y-1">
                        <p className="font-medium">{protocol.name}</p>
                        {protocol.description && (
                          <p className="max-w-xl text-xs text-muted-foreground">{protocol.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 align-top font-mono text-xs text-muted-foreground">{protocol.slug}</td>
                    <td className="px-4 py-4 align-top">
                      {protocol.assay_family ? <span className="stat-pill">{protocol.assay_family}</span> : <span className="text-muted-foreground">-</span>}
                    </td>
                    <td className="px-4 py-4 align-top text-muted-foreground">{protocol.molecule_type ?? '-'}</td>
                    <td className="px-4 py-4 align-top">
                      <ConfidenceScore score={protocol.confidence_score} />
                    </td>
                    <td className="px-4 py-4 align-top">
                      <ReviewStatusBadge status={protocol.review_status} />
                    </td>
                    <td className="px-4 py-4 align-top text-muted-foreground">
                      <ChevronRight className="h-4 w-4" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="space-y-3 md:hidden">
            {filtered.map((protocol) => (
              <button
                key={protocol.slug}
                onClick={() => navigate(`/protocols/${protocol.slug}`)}
                className="section-card flex w-full flex-col gap-3 text-left transition-colors hover:border-foreground/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{protocol.name}</p>
                    <p className="mt-1 font-mono text-[11px] text-muted-foreground">{protocol.slug}</p>
                  </div>
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                </div>

                {protocol.description && (
                  <p className="text-xs text-muted-foreground">{protocol.description}</p>
                )}

                <div className="flex flex-wrap gap-2">
                  {protocol.assay_family && <span className="stat-pill">{protocol.assay_family}</span>}
                  {protocol.molecule_type && <span className="stat-pill">{protocol.molecule_type}</span>}
                  <ConfidenceScore score={protocol.confidence_score} />
                  <ReviewStatusBadge status={protocol.review_status} />
                </div>
              </button>
            ))}
          </section>

          <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Showing {filtered.length} of {protocols.length} protocols
          </p>
        </>
      )}
    </div>
  );
}
