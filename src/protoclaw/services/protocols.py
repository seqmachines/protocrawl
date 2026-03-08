from protoclaw.db.tables import ProtocolRow
from protoclaw.models import (
    Adapter,
    BarcodeSpec,
    Citation,
    FailureMode,
    LibraryRegion,
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


def row_to_protocol(row: ProtocolRow) -> Protocol:
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
        library_structure=[
            LibraryRegion(**r) for r in (row.library_structure or [])
        ] or None,
        source_urls=row.source_urls,
        confidence_score=row.confidence_score,
        review_status=ReviewStatus(row.review_status),
        extraction_notes=row.extraction_notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        published_at=row.published_at,
        schema_version=row.schema_version,
    )
