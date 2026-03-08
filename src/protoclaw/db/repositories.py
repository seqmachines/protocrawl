import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from protoclaw.db.tables import (
    AdapterRow,
    BarcodeSpecRow,
    CitationRow,
    FailureModeRow,
    IngestionRunRow,
    ProtocolCitationRow,
    ProtocolRow,
    ProtocolSeqSpecRow,
    ProtocolSubmissionRow,
    ProtocolVersionRow,
    QCExpectationRow,
    ReadSegmentRow,
    ReagentKitRow,
    ReviewRequestRow,
    SourceDocumentRow,
)
from protoclaw.models import (
    IngestionRun,
    Protocol,
    ProtocolSubmission,
    ReviewRequest,
    SourceDocument,
)


def _protocol_row_from_model(p: Protocol) -> ProtocolRow:
    return ProtocolRow(
        id=p.id,
        slug=p.slug,
        name=p.name,
        version=p.version,
        assay_family=p.assay_family.value,
        molecule_type=p.molecule_type.value,
        description=p.description,
        vendor=p.vendor,
        platform=p.platform,
        read_type=p.read_geometry.read_type.value,
        read1_length=p.read_geometry.read1_length,
        read2_length=p.read_geometry.read2_length,
        index1_length=p.read_geometry.index1_length,
        index2_length=p.read_geometry.index2_length,
        protocol_steps=p.protocol_steps,
        caveats=p.caveats,
        source_urls=p.source_urls,
        confidence_score=p.confidence_score,
        review_status=p.review_status.value,
        extraction_notes=p.extraction_notes,
        library_structure=[r.model_dump() for r in p.library_structure] if p.library_structure else None,
        created_at=p.created_at,
        updated_at=p.updated_at,
        published_at=p.published_at,
        schema_version=p.schema_version,
        read_segments=[
            ReadSegmentRow(
                role=s.role.value,
                read_number=s.read_number,
                start_pos=s.start_pos,
                length=s.length,
                sequence=s.sequence,
                description=s.description,
            )
            for s in p.read_geometry.segments
        ],
        adapters=[
            AdapterRow(name=a.name, sequence=a.sequence, position=a.position)
            for a in p.adapters
        ],
        barcodes=[
            BarcodeSpecRow(
                role=b.role.value,
                length=b.length,
                whitelist_source=b.whitelist_source,
                addition_method=b.addition_method,
            )
            for b in p.barcodes
        ],
        reagent_kits=[
            ReagentKitRow(
                name=r.name,
                vendor=r.vendor,
                catalog_number=r.catalog_number,
                version=r.version,
            )
            for r in p.reagent_kits
        ],
        qc_expectations=[
            QCExpectationRow(
                metric=q.metric,
                typical_range_low=q.typical_range_low,
                typical_range_high=q.typical_range_high,
                notes=q.notes,
            )
            for q in p.qc_expectations
        ],
        failure_modes=[
            FailureModeRow(
                description=f.description,
                symptom=f.symptom,
                likely_cause=f.likely_cause,
                mitigation=f.mitigation,
            )
            for f in p.failure_modes
        ],
    )


_PROTOCOL_EAGER_OPTIONS = [
    selectinload(ProtocolRow.read_segments),
    selectinload(ProtocolRow.adapters),
    selectinload(ProtocolRow.barcodes),
    selectinload(ProtocolRow.reagent_kits),
    selectinload(ProtocolRow.qc_expectations),
    selectinload(ProtocolRow.failure_modes),
    selectinload(ProtocolRow.citations),
]

_SUBMISSION_EAGER_OPTIONS = [
    selectinload(ProtocolSubmissionRow.source_document),
    selectinload(ProtocolSubmissionRow.protocol),
    selectinload(ProtocolSubmissionRow.review_request),
    selectinload(ProtocolSubmissionRow.runs),
]


async def create_protocol(session: AsyncSession, protocol: Protocol) -> ProtocolRow:
    row = _protocol_row_from_model(protocol)
    session.add(row)

    # Handle citations (many-to-many)
    for c in protocol.citations:
        citation_row = CitationRow(
            doi=c.doi,
            pmid=c.pmid,
            arxiv_id=c.arxiv_id,
            title=c.title,
            authors=c.authors,
            year=c.year,
            url=c.url,
        )
        session.add(citation_row)
        await session.flush()
        session.add(
            ProtocolCitationRow(protocol_id=row.id, citation_id=citation_row.id)
        )

    await session.flush()
    return row


async def get_protocol_by_slug(session: AsyncSession, slug: str) -> ProtocolRow | None:
    stmt = (
        select(ProtocolRow)
        .options(*_PROTOCOL_EAGER_OPTIONS)
        .where(ProtocolRow.slug == slug)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_protocol_by_id(
    session: AsyncSession, protocol_id: uuid.UUID
) -> ProtocolRow | None:
    stmt = (
        select(ProtocolRow)
        .options(*_PROTOCOL_EAGER_OPTIONS)
        .where(ProtocolRow.id == protocol_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_protocols(
    session: AsyncSession,
    assay_family: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ProtocolRow]:
    stmt = select(ProtocolRow).options(*_PROTOCOL_EAGER_OPTIONS)
    if assay_family:
        stmt = stmt.where(ProtocolRow.assay_family == assay_family)
    stmt = stmt.order_by(ProtocolRow.name).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_protocols(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 5,
) -> list[ProtocolRow]:
    stmt = (
        select(ProtocolRow)
        .options(*_PROTOCOL_EAGER_OPTIONS)
        .where(
            (ProtocolRow.slug.ilike(f"%{query}%"))
            | (ProtocolRow.name.ilike(f"%{query}%"))
        )
        .order_by(ProtocolRow.confidence_score.desc(), ProtocolRow.name)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_review_request(
    session: AsyncSession, review: ReviewRequest
) -> ReviewRequestRow:
    row = ReviewRequestRow(
        id=review.id,
        protocol_id=review.protocol_id,
        confidence_score=review.confidence_score,
        extraction_notes=review.extraction_notes,
        status=review.status.value,
        assigned_to=review.assigned_to,
        created_at=review.created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def list_pending_reviews(session: AsyncSession) -> list[ReviewRequestRow]:
    stmt = (
        select(ReviewRequestRow)
        .options(selectinload(ReviewRequestRow.protocol))
        .where(ReviewRequestRow.status == "pending")
        .order_by(ReviewRequestRow.created_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_source_document(
    session: AsyncSession, source: SourceDocument
) -> SourceDocumentRow:
    row = SourceDocumentRow(
        id=source.id,
        url=source.url,
        title=source.title,
        source_type=source.source_type,
        content_hash=source.content_hash,
        raw_text=source.raw_text,
        metadata_json=source.metadata,
        discovered_at=source.discovered_at,
        fetched_at=source.fetched_at,
    )
    session.add(row)
    await session.flush()
    return row


async def get_review_by_id(
    session: AsyncSession, review_id: uuid.UUID
) -> ReviewRequestRow | None:
    stmt = (
        select(ReviewRequestRow)
        .options(selectinload(ReviewRequestRow.protocol))
        .where(ReviewRequestRow.id == review_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_review_status(
    session: AsyncSession,
    review_id: uuid.UUID,
    status: str,
    *,
    protocol_published: bool = False,
) -> ReviewRequestRow | None:
    """Update a review request status and optionally publish the protocol."""
    review = await get_review_by_id(session, review_id)
    if not review:
        return None

    review.status = status

    if protocol_published and status == "approved":
        protocol = await get_protocol_by_id(session, review.protocol_id)
        if protocol:
            protocol.review_status = "approved"
            protocol.published_at = datetime.utcnow()

    await session.flush()
    return review


async def create_protocol_version(
    session: AsyncSession,
    protocol_id: uuid.UUID,
    snapshot: dict,
    *,
    change_summary: str | None = None,
    created_by: str = "system",
) -> ProtocolVersionRow:
    """Save a versioned snapshot of a protocol."""
    # Get next version number
    stmt = (
        select(ProtocolVersionRow.version_number)
        .where(ProtocolVersionRow.protocol_id == protocol_id)
        .order_by(ProtocolVersionRow.version_number.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    latest = result.scalar_one_or_none()
    next_version = (latest or 0) + 1

    row = ProtocolVersionRow(
        protocol_id=protocol_id,
        version_number=next_version,
        snapshot=snapshot,
        change_summary=change_summary,
        created_by=created_by,
    )
    session.add(row)

    # Update version_number on the protocol itself
    protocol = await get_protocol_by_id(session, protocol_id)
    if protocol:
        protocol.version_number = next_version

    await session.flush()
    return row


async def list_protocol_versions(
    session: AsyncSession, protocol_id: uuid.UUID
) -> list[ProtocolVersionRow]:
    """List all versions of a protocol, newest first."""
    stmt = (
        select(ProtocolVersionRow)
        .where(ProtocolVersionRow.protocol_id == protocol_id)
        .order_by(ProtocolVersionRow.version_number.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_protocol_submission(
    session: AsyncSession, submission: ProtocolSubmission
) -> ProtocolSubmissionRow:
    row = ProtocolSubmissionRow(
        id=submission.id,
        source_url=submission.source_url,
        notes=submission.notes,
        submitted_by=submission.submitted_by,
        status=submission.status.value,
        source_document_id=submission.source_document_id,
        protocol_id=submission.protocol_id,
        review_request_id=submission.review_request_id,
        error_message=submission.error_message,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )
    session.add(row)
    await session.flush()
    return row


async def get_submission_by_id(
    session: AsyncSession, submission_id: uuid.UUID
) -> ProtocolSubmissionRow | None:
    stmt = (
        select(ProtocolSubmissionRow)
        .options(*_SUBMISSION_EAGER_OPTIONS)
        .where(ProtocolSubmissionRow.id == submission_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_submissions(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[ProtocolSubmissionRow]:
    stmt = (
        select(ProtocolSubmissionRow)
        .options(*_SUBMISSION_EAGER_OPTIONS)
        .order_by(ProtocolSubmissionRow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_submission(
    session: AsyncSession,
    submission_id: uuid.UUID,
    *,
    status: str | None = None,
    source_document_id: uuid.UUID | None = None,
    protocol_id: uuid.UUID | None = None,
    review_request_id: uuid.UUID | None = None,
    error_message: str | None = None,
) -> ProtocolSubmissionRow | None:
    submission = await get_submission_by_id(session, submission_id)
    if not submission:
        return None

    if status is not None:
        submission.status = status
    if source_document_id is not None:
        submission.source_document_id = source_document_id
    if protocol_id is not None:
        submission.protocol_id = protocol_id
    if review_request_id is not None:
        submission.review_request_id = review_request_id
    submission.error_message = error_message
    submission.updated_at = datetime.utcnow()
    await session.flush()
    return submission


async def create_ingestion_run(
    session: AsyncSession, run: IngestionRun
) -> IngestionRunRow:
    row = IngestionRunRow(
        id=run.id,
        submission_id=run.submission_id,
        status=run.status.value,
        stage=run.stage,
        results=run.results,
        errors=run.errors,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )
    session.add(row)
    await session.flush()
    return row


async def get_ingestion_run_by_id(
    session: AsyncSession, run_id: uuid.UUID
) -> IngestionRunRow | None:
    stmt = select(IngestionRunRow).where(IngestionRunRow.id == run_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_ingestion_runs_for_submission(
    session: AsyncSession, submission_id: uuid.UUID
) -> list[IngestionRunRow]:
    stmt = (
        select(IngestionRunRow)
        .where(IngestionRunRow.submission_id == submission_id)
        .order_by(IngestionRunRow.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_ingestion_run(
    session: AsyncSession,
    run_id: uuid.UUID,
    *,
    status: str | None = None,
    stage: str | None = None,
    results: dict | None = None,
    errors: list[str] | None = None,
    completed_at: datetime | None = None,
) -> IngestionRunRow | None:
    run = await get_ingestion_run_by_id(session, run_id)
    if not run:
        return None

    if status is not None:
        run.status = status
    if stage is not None:
        run.stage = stage
    if results is not None:
        run.results = results
    if errors is not None:
        run.errors = errors
    run.completed_at = completed_at
    await session.flush()
    return run


async def upsert_protocol_seqspec(
    session: AsyncSession,
    *,
    protocol_id: uuid.UUID,
    submission_id: uuid.UUID | None,
    content_json: dict,
    content_yaml: str,
) -> ProtocolSeqSpecRow:
    stmt = select(ProtocolSeqSpecRow).where(ProtocolSeqSpecRow.protocol_id == protocol_id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        row = ProtocolSeqSpecRow(
            protocol_id=protocol_id,
            submission_id=submission_id,
            content_json=content_json,
            content_yaml=content_yaml,
        )
        session.add(row)
    else:
        row.submission_id = submission_id
        row.content_json = content_json
        row.content_yaml = content_yaml
    await session.flush()
    return row


async def get_protocol_seqspec(
    session: AsyncSession, protocol_id: uuid.UUID
) -> ProtocolSeqSpecRow | None:
    stmt = select(ProtocolSeqSpecRow).where(ProtocolSeqSpecRow.protocol_id == protocol_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
