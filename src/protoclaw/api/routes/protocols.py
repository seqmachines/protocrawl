from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from protoclaw.api.dependencies import get_db
from protoclaw.db import repositories as repo
from protoclaw.db.tables import ProtocolRow
from protoclaw.models import (
    Adapter,
    BarcodeSpec,
    Citation,
    FailureMode,
    Protocol,
    QCExpectation,
    ReadGeometry,
    ReadSegment,
    ReagentKit,
)
from protoclaw.models.enums import (
    AssayFamily,
    MoleculeType,
    ReadType,
    ReviewStatus,
    SegmentRole,
)

router = APIRouter()


def _row_to_protocol(row: ProtocolRow) -> Protocol:
    """Convert a SQLAlchemy ORM row to a Pydantic Protocol model."""
    return Protocol(
        id=row.id,
        slug=row.slug,
        name=row.name,
        version=row.version,
        assay_family=AssayFamily(row.assay_family),
        molecule_type=MoleculeType(row.molecule_type),
        description=row.description,
        vendor=row.vendor,
        platform=row.platform,
        read_geometry=ReadGeometry(
            read_type=ReadType(row.read_type),
            read1_length=row.read1_length,
            read2_length=row.read2_length,
            index1_length=row.index1_length,
            index2_length=row.index2_length,
            segments=[
                ReadSegment(
                    role=SegmentRole(s.role),
                    read_number=s.read_number,
                    start_pos=s.start_pos,
                    length=s.length,
                    sequence=s.sequence,
                    description=s.description,
                )
                for s in row.read_segments
            ],
        ),
        adapters=[
            Adapter(name=a.name, sequence=a.sequence, position=a.position)
            for a in row.adapters
        ],
        barcodes=[
            BarcodeSpec(
                role=SegmentRole(b.role),
                length=b.length,
                whitelist_source=b.whitelist_source,
                addition_method=b.addition_method,
            )
            for b in row.barcodes
        ],
        reagent_kits=[
            ReagentKit(
                name=r.name,
                vendor=r.vendor,
                catalog_number=r.catalog_number,
                version=r.version,
            )
            for r in row.reagent_kits
        ],
        citations=[
            Citation(
                doi=c.doi,
                pmid=c.pmid,
                arxiv_id=c.arxiv_id,
                title=c.title,
                authors=c.authors,
                year=c.year,
                url=c.url,
            )
            for c in row.citations
        ],
        qc_expectations=[
            QCExpectation(
                metric=q.metric,
                typical_range_low=q.typical_range_low,
                typical_range_high=q.typical_range_high,
                notes=q.notes,
            )
            for q in row.qc_expectations
        ],
        failure_modes=[
            FailureMode(
                description=f.description,
                symptom=f.symptom,
                likely_cause=f.likely_cause,
                mitigation=f.mitigation,
            )
            for f in row.failure_modes
        ],
        protocol_steps=row.protocol_steps,
        caveats=row.caveats,
        source_urls=row.source_urls,
        confidence_score=row.confidence_score,
        review_status=ReviewStatus(row.review_status),
        extraction_notes=row.extraction_notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
        schema_version=row.schema_version,
    )


@router.get("")
async def list_protocols(
    assay_family: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = await repo.list_protocols(
        db, assay_family=assay_family, limit=limit, offset=offset
    )
    return [
        _row_to_protocol(r).model_dump(
            mode="json",
            include={
                "id",
                "slug",
                "name",
                "version",
                "assay_family",
                "molecule_type",
                "vendor",
                "description",
                "confidence_score",
                "review_status",
            },
        )
        for r in rows
    ]


@router.get("/{slug}")
async def get_protocol(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = await repo.get_protocol_by_slug(db, slug)
    if not row:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return _row_to_protocol(row).model_dump(mode="json")


@router.get("/{slug}/read-geometry")
async def get_read_geometry(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = await repo.get_protocol_by_slug(db, slug)
    if not row:
        raise HTTPException(status_code=404, detail="Protocol not found")
    protocol = _row_to_protocol(row)
    return protocol.read_geometry.model_dump(mode="json")


@router.get("/{slug}/versions")
async def list_versions(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    row = await repo.get_protocol_by_slug(db, slug)
    if not row:
        raise HTTPException(status_code=404, detail="Protocol not found")
    versions = await repo.list_protocol_versions(db, row.id)
    return [
        {
            "version_number": v.version_number,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat(),
            "created_by": v.created_by,
        }
        for v in versions
    ]
