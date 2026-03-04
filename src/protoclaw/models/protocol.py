from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from protoclaw.models.enums import (
    AssayFamily,
    ConfidenceLevel,
    MoleculeType,
    ReadType,
    ReviewStatus,
    SegmentRole,
)


class ReadSegment(BaseModel):
    """A contiguous region within a sequencing read."""

    role: SegmentRole
    read_number: int  # 1=Read1, 2=Read2, 3=Index1, 4=Index2
    start_pos: int  # 0-based position within the read
    length: int | None = None  # None = variable length
    sequence: str | None = None  # Fixed sequence if known (e.g., linker)
    description: str | None = None


class ReadGeometry(BaseModel):
    """Complete read layout for a protocol."""

    read_type: ReadType
    read1_length: int | None = None
    read2_length: int | None = None
    index1_length: int | None = None
    index2_length: int | None = None
    segments: list[ReadSegment] = []


class Adapter(BaseModel):
    name: str  # e.g., "Illumina P5", "TruSeq Read 1"
    sequence: str
    position: str  # "5prime" | "3prime" | "internal"


class BarcodeSpec(BaseModel):
    """Barcode/UMI specification."""

    role: SegmentRole  # cell_barcode, umi, sample_index, feature_barcode
    length: int
    whitelist_source: str | None = None  # URL or filename of barcode whitelist
    addition_method: str | None = None  # "ligation", "PCR", "template_switch", etc.


class ReagentKit(BaseModel):
    name: str
    vendor: str
    catalog_number: str | None = None
    version: str | None = None


class Citation(BaseModel):
    doi: str | None = None
    pmid: str | None = None
    arxiv_id: str | None = None
    title: str
    authors: list[str] = []
    year: int | None = None
    url: str | None = None


class QCExpectation(BaseModel):
    metric: str  # e.g., "reads_per_cell", "genes_per_cell"
    typical_range_low: float | None = None
    typical_range_high: float | None = None
    notes: str | None = None


class FailureMode(BaseModel):
    description: str
    symptom: str
    likely_cause: str
    mitigation: str | None = None


def _confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.85:
        return ConfidenceLevel.HIGH
    if score >= 0.60:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


class Protocol(BaseModel):
    """The canonical protocol record."""

    id: UUID = Field(default_factory=uuid4)
    slug: str  # URL-friendly identifier, e.g., "10x-chromium-3prime-v3"
    name: str
    version: str  # Protocol version (e.g., "v3.1")
    assay_family: AssayFamily
    molecule_type: MoleculeType
    description: str  # 2-3 sentence summary
    vendor: str | None = None
    platform: str | None = None  # e.g., "Illumina NovaSeq"

    read_geometry: ReadGeometry
    adapters: list[Adapter] = []
    barcodes: list[BarcodeSpec] = []
    reagent_kits: list[ReagentKit] = []
    protocol_steps: list[str] = []  # High-level workflow steps
    qc_expectations: list[QCExpectation] = []
    failure_modes: list[FailureMode] = []
    caveats: list[str] = []

    citations: list[Citation] = []
    source_urls: list[str] = []

    confidence_score: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.PENDING
    extraction_notes: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: datetime | None = None
    schema_version: str = "1.0.0"

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return _confidence_level(self.confidence_score)
