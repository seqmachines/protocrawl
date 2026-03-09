const DEFAULT_DEV_BASE_URL = 'http://127.0.0.1:8000';
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? DEFAULT_DEV_BASE_URL : '')
).replace(/\/+$/, '');

function joinUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

async function parseErrorBody(res: Response): Promise<string> {
  const text = await res.text().catch(() => res.statusText);
  const compact = text.trim();

  if (!compact) {
    return res.statusText;
  }

  if (compact.startsWith('<')) {
    if (compact.toLowerCase().includes('ngrok')) {
      return 'Received HTML from ngrok instead of JSON. Confirm the tunnel is active and that the request includes the ngrok skip-browser-warning header.';
    }
    return 'Received HTML instead of JSON from the API.';
  }

  return compact;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  headers.set('Accept', 'application/json');
  headers.set('ngrok-skip-browser-warning', 'true');

  const hasBody = options?.body !== undefined && options?.body !== null;
  const isFormData = typeof FormData !== 'undefined' && options?.body instanceof FormData;
  if (hasBody && !isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(joinUrl(path), {
    ...options,
    headers,
  });

  if (!res.ok) {
    throw new Error(`${res.status}: ${await parseErrorBody(res)}`);
  }

  const contentType = res.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    const body = await res.text().catch(() => '');
    if (body.trim().startsWith('<')) {
      throw new Error(
        'Expected JSON but received HTML. This usually means the request hit an ngrok browser warning page or an HTML route like /reviews.',
      );
    }
    throw new Error(`Expected JSON but received ${contentType || 'an unknown content type'}.`);
  }

  return res.json() as Promise<T>;
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'needs_revision';
export type SubmissionStatus = 'queued' | 'running' | 'completed' | 'failed';
export type SegmentRole =
  | 'cell_barcode'
  | 'umi'
  | 'cdna'
  | 'sample_index'
  | 'linker'
  | 'spacer'
  | 'primer'
  | 'adapter'
  | 'feature_barcode'
  | 'genomic_insert'
  | 'other';

export interface ProtocolListItem {
  id?: string;
  slug: string;
  name: string;
  version?: string;
  assay_family?: string | null;
  molecule_type?: string | null;
  vendor?: string | null;
  description?: string | null;
  confidence_score?: number | null;
  review_status?: ReviewStatus | null;
}

export interface ReadSegment {
  role: SegmentRole;
  read_number: number;
  start_pos: number;
  length?: number | null;
  sequence?: string | null;
  description?: string | null;
}

export interface ReadGeometry {
  read_type?: string | null;
  read1_length?: number | null;
  read2_length?: number | null;
  index1_length?: number | null;
  index2_length?: number | null;
  segments: ReadSegment[];
}

export interface Adapter {
  name: string;
  sequence: string;
  position: string;
}

export interface Barcode {
  role: SegmentRole;
  length: number;
  whitelist_source?: string | null;
  addition_method?: string | null;
}

export interface Citation {
  doi?: string | null;
  pmid?: string | null;
  arxiv_id?: string | null;
  title: string;
  authors: string[];
  year?: number | null;
  url?: string | null;
}

export interface ReagentKit {
  name: string;
  vendor: string;
  catalog_number?: string | null;
  version?: string | null;
}

export interface QCExpectation {
  metric: string;
  typical_range_low?: number | null;
  typical_range_high?: number | null;
  notes?: string | null;
}

export interface FailureMode {
  description: string;
  symptom: string;
  likely_cause: string;
  mitigation?: string | null;
}

export interface LibraryRegion {
  type: string;
  top: string;
  bottom: string;
  label?: string | null;
}

export interface ProtocolDetail extends ProtocolListItem {
  platform?: string | null;
  read_geometry: ReadGeometry;
  adapters: Adapter[];
  barcodes: Barcode[];
  reagent_kits: ReagentKit[];
  protocol_steps: string[];
  qc_expectations: QCExpectation[];
  failure_modes: FailureMode[];
  caveats: string[];
  citations: Citation[];
  source_urls: string[];
  library_structure?: LibraryRegion[] | null;
  extraction_notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  published_at?: string | null;
  schema_version?: string | null;
}

export interface IngestionRun {
  id: string;
  status: SubmissionStatus;
  stage?: string | null;
  results?: Record<string, unknown> | null;
  errors?: string[] | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface Submission {
  id: string;
  source_url: string;
  notes?: string | null;
  submitted_by?: string | null;
  status: SubmissionStatus;
  source_document_id?: string | null;
  protocol_id?: string | null;
  protocol_slug?: string | null;
  review_request_id?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  latest_run?: IngestionRun | null;
}

export const api = {
  health: () => requestJson<Record<string, unknown>>('/health'),
  protocols: {
    list: (params?: { assay_family?: string; limit?: number; offset?: number }) => {
      const qs = new URLSearchParams();
      if (params?.assay_family) qs.set('assay_family', params.assay_family);
      if (params?.limit != null) qs.set('limit', String(params.limit));
      if (params?.offset != null) qs.set('offset', String(params.offset));
      const query = qs.toString();
      return requestJson<ProtocolListItem[]>(query ? `/protocols?${query}` : '/protocols');
    },
    get: (slug: string) => requestJson<ProtocolDetail>(`/protocols/${slug}`),
    readGeometry: (slug: string) =>
      requestJson<ReadGeometry>(`/protocols/${slug}/read-geometry`),
    seqspec: (slug: string) => requestJson<unknown>(`/protocols/${slug}/seqspec`),
  },
  submissions: {
    list: (params?: { limit?: number; offset?: number }) => {
      const qs = new URLSearchParams();
      if (params?.limit != null) qs.set('limit', String(params.limit));
      if (params?.offset != null) qs.set('offset', String(params.offset));
      const query = qs.toString();
      return requestJson<Submission[]>(query ? `/submissions?${query}` : '/submissions');
    },
    get: (id: string) => requestJson<Submission>(`/submissions/${id}`),
  },
};
