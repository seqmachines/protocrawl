import { useState } from 'react';
import { Dna } from 'lucide-react';
import type { LibraryRegion } from '@/lib/api';

const REGION_COLORS: Record<string, { bg: string; fg: string; border: string }> = {
  p5:      { bg: '#dbe9f6', fg: '#08519c', border: '#08519c' },
  p7:      { bg: '#fde0dc', fg: '#a50f15', border: '#a50f15' },
  s5:      { bg: '#d4eaf7', fg: '#2171b5', border: '#6baed6' },
  s7:      { bg: '#fde4d8', fg: '#b44a1a', border: '#fc9272' },
  cbc:     { bg: '#fce4ee', fg: '#c2185b', border: '#f768a1' },
  umi:     { bg: '#ede7f6', fg: '#5e35b1', border: '#807dba' },
  me:      { bg: '#f0f0f0', fg: '#616161', border: '#969696' },
  tso:     { bg: '#e0f2e9', fg: '#1b7340', border: '#2ca25f' },
  cdna:    { bg: '#f5f5f5', fg: '#424242', border: '#9e9e9e' },
  index:   { bg: '#fff3e0', fg: '#e65100', border: '#e6550d' },
  linker:  { bg: '#f5f5f5', fg: '#757575', border: '#bdbdbd' },
  poly_dt: { bg: '#e8f5e9', fg: '#2e7d32', border: '#74c476' },
  poly_a:  { bg: '#e8f5e9', fg: '#2e7d32', border: '#74c476' },
  nexus:   { bg: '#fce4ec', fg: '#7e331f', border: '#f0b7a6' },
  hairp:   { bg: '#ede7f6', fg: '#4a148c', border: '#bcb6c9' },
};

const DEFAULT_COLOR = { bg: '#f5f5f5', fg: '#424242', border: '#9e9e9e' };

function getColor(type: string) {
  return REGION_COLORS[type] ?? DEFAULT_COLOR;
}

/** Compute a flex-basis weight: longer sequences get more space, but capped. */
function regionWeight(region: LibraryRegion): number {
  const len = region.top.length;
  if (len <= 10) return 1;
  if (len <= 20) return 2;
  if (len <= 30) return 3;
  return 4;
}

function RegionBlock({
  region,
  isActive,
  onHover,
  onLeave,
}: {
  region: LibraryRegion;
  isActive: boolean;
  onHover: () => void;
  onLeave: () => void;
}) {
  const color = getColor(region.type);
  const weight = regionWeight(region);

  return (
    <div
      className="relative flex flex-col items-center transition-all duration-150"
      style={{ flex: `${weight} 1 0%`, minWidth: 48 }}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      {/* Label above */}
      <div
        className="mb-1.5 w-full text-center font-mono text-[10px] font-semibold leading-tight tracking-wide"
        style={{ color: color.fg }}
      >
        {region.label ?? region.type}
      </div>

      {/* Cartoon block */}
      <div
        className="relative w-full overflow-hidden transition-shadow duration-150"
        style={{
          backgroundColor: color.bg,
          border: `1.5px solid ${color.border}`,
          borderRadius: 3,
          boxShadow: isActive
            ? `0 0 0 2px ${color.border}40, 0 2px 8px ${color.border}30`
            : 'none',
        }}
      >
        {/* Top strand */}
        <div
          className="border-b px-1.5 py-1 font-mono text-[10px] leading-tight"
          style={{
            color: color.fg,
            borderColor: `${color.border}40`,
          }}
        >
          <span className="opacity-50">5&prime;</span>{' '}
          <span className="select-all">{region.top}</span>
        </div>

        {/* Bottom strand */}
        <div
          className="px-1.5 py-1 font-mono text-[10px] leading-tight"
          style={{ color: color.fg }}
        >
          <span className="opacity-50">3&prime;</span>{' '}
          <span className="select-all">{region.bottom}</span>
        </div>
      </div>

      {/* Length indicator below */}
      <div className="mt-1 font-mono text-[9px] text-muted-foreground">
        {region.top.replace(/\./g, '').length > 6
          ? `${region.top.length} nt`
          : ''}
      </div>
    </div>
  );
}

function SectionTitle({ label }: { label: string }) {
  return (
    <div className="mb-4 flex items-center gap-3 border-b border-border pb-3">
      <span className="flex h-9 w-9 items-center justify-center border border-border bg-background">
        <Dna className="h-4 w-4" />
      </span>
      <div>
        <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
          Section
        </p>
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">{label}</h2>
      </div>
    </div>
  );
}

export function LibraryStructureSection({ regions }: { regions: LibraryRegion[] }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (!regions.length) return null;

  return (
    <section className="section-card">
      <SectionTitle label="Final library structure" />

      {/* Cartoon diagram */}
      <div className="overflow-x-auto border border-border bg-background p-4">
        {/* Strand direction labels */}
        <div className="mb-1 flex items-center justify-between px-1">
          <span className="font-mono text-[10px] font-semibold text-muted-foreground">5&prime;</span>
          <span className="font-mono text-[10px] font-semibold text-muted-foreground">3&prime;</span>
        </div>

        {/* Region blocks */}
        <div className="flex gap-[2px]" style={{ minWidth: 'max-content' }}>
          {regions.map((region, i) => (
            <RegionBlock
              key={i}
              region={region}
              isActive={activeIndex === i}
              onHover={() => setActiveIndex(i)}
              onLeave={() => setActiveIndex(null)}
            />
          ))}
        </div>

        {/* Bottom strand direction */}
        <div className="mt-0.5 flex items-center justify-between px-1">
          <span className="font-mono text-[10px] font-semibold text-muted-foreground">3&prime;</span>
          <span className="font-mono text-[10px] font-semibold text-muted-foreground">5&prime;</span>
        </div>
      </div>

      {/* Full sequence text view */}
      <details className="mt-3">
        <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground">
          Show full sequence
        </summary>
        <div className="mt-2 overflow-x-auto border border-border bg-background p-3">
          <pre className="font-mono text-[12px] leading-[1.7] whitespace-pre">
            <span className="text-muted-foreground">{"5'- "}</span>
            {regions.map((region, i) => (
              <span key={i} style={{ color: getColor(region.type).fg }}>
                {region.top}
              </span>
            ))}
            <span className="text-muted-foreground">{" -3'"}</span>
            {'\n'}
            <span className="text-muted-foreground">{"3'- "}</span>
            {regions.map((region, i) => (
              <span key={i} style={{ color: getColor(region.type).fg }}>
                {region.bottom}
              </span>
            ))}
            <span className="text-muted-foreground">{" -5'"}</span>
          </pre>
        </div>
      </details>
    </section>
  );
}
