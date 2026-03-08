from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable

from protoclaw.agents.formatter.tools import (
    format_protocol,
    generate_seqspec_json,
    generate_seqspec_yaml,
)
from protoclaw.agents.normalizer.tools import seqspec_to_protocol
from protoclaw.agents.parser.tools import (
    extract_seqspec,
)
from protoclaw.agents.publisher.tools import publish_protocol
from protoclaw.agents.source_scout.tools import fetch_page_text
from protoclaw.db.engine import async_session
from protoclaw.db import repositories as repo
from protoclaw.models import (
    IngestionRun,
    IngestionStatus,
    ProtocolSubmission,
    SeqSpec,
    SourceDocument,
)


Fetcher = Callable[[str], Awaitable[SourceDocument | dict]]
SeqSpecExtractor = Callable[[str, list[str] | None], Awaitable[SeqSpec]]
Publisher = Callable[[str], Awaitable[dict]]


@dataclass(slots=True)
class IngestionToolkit:
    fetch_source: Fetcher = fetch_page_text
    extract_seqspec: SeqSpecExtractor = extract_seqspec
    publish_protocol: Publisher = publish_protocol


def serialize_run(run: repo.IngestionRunRow) -> dict:
    return {
        "id": str(run.id),
        "status": run.status,
        "stage": run.stage,
        "results": run.results,
        "errors": run.errors,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def serialize_submission(submission: repo.ProtocolSubmissionRow) -> dict:
    latest_run = submission.runs[0] if submission.runs else None
    protocol_slug = submission.protocol.slug if submission.protocol else None
    return {
        "id": str(submission.id),
        "source_url": submission.source_url,
        "notes": submission.notes,
        "submitted_by": submission.submitted_by,
        "status": submission.status,
        "source_document_id": (
            str(submission.source_document_id) if submission.source_document_id else None
        ),
        "protocol_id": str(submission.protocol_id) if submission.protocol_id else None,
        "protocol_slug": protocol_slug,
        "review_request_id": (
            str(submission.review_request_id) if submission.review_request_id else None
        ),
        "error_message": submission.error_message,
        "created_at": submission.created_at.isoformat(),
        "updated_at": submission.updated_at.isoformat(),
        "latest_run": serialize_run(latest_run) if latest_run else None,
    }


async def create_submission(
    source_url: str,
    *,
    notes: str | None = None,
    submitted_by: str = "api",
) -> dict:
    submission = ProtocolSubmission(
        source_url=source_url,
        notes=notes,
        submitted_by=submitted_by,
    )
    async with async_session() as session:
        await repo.create_protocol_submission(session, submission)
        await session.commit()
        row = await repo.get_submission_by_id(session, submission.id)
        assert row is not None
        return serialize_submission(row)


async def create_submission_and_ingest(
    source_url: str,
    *,
    notes: str | None = None,
    submitted_by: str = "api",
    toolkit: IngestionToolkit | None = None,
) -> dict:
    submission = await create_submission(
        source_url,
        notes=notes,
        submitted_by=submitted_by,
    )
    return await ingest_submission(uuid.UUID(submission["id"]), toolkit=toolkit)


async def ingest_submission(
    submission_id: uuid.UUID,
    *,
    toolkit: IngestionToolkit | None = None,
) -> dict:
    tools = toolkit or IngestionToolkit()
    run = IngestionRun(submission_id=submission_id)

    async with async_session() as session:
        await repo.create_ingestion_run(session, run)
        await repo.update_submission(
            session,
            submission_id,
            status=IngestionStatus.RUNNING.value,
            error_message=None,
        )
        await repo.update_ingestion_run(
            session,
            run.id,
            status=IngestionStatus.RUNNING.value,
            stage="fetching_source",
            results={},
            errors=[],
        )
        await session.commit()

    stage_results: dict = {}

    try:
        async with async_session() as session:
            submission = await repo.get_submission_by_id(session, submission_id)
            if submission is None:
                raise ValueError(f"Submission {submission_id} not found")
            source_url = submission.source_url

        source_result = await tools.fetch_source(source_url)
        if isinstance(source_result, SourceDocument):
            source_doc = source_result
        else:
            source_result.setdefault("url", source_url)
            source_result.setdefault("source_type", "vendor_docs")
            source_result.setdefault("fetched_at", datetime.utcnow().isoformat())
            source_doc = SourceDocument.model_validate(source_result)
        stage_results["source_document"] = source_doc.model_dump(mode="json")

        async with async_session() as session:
            stored_source = await repo.create_source_document(session, source_doc)
            await repo.update_submission(
                session,
                submission_id,
                source_document_id=stored_source.id,
            )
            await repo.update_ingestion_run(
                session,
                run.id,
                stage="parsing",
                results=stage_results,
            )
            await session.commit()

        source_text = source_doc.raw_text or ""
        if not source_text.strip():
            raise ValueError(f"Source {source_url} did not yield readable text")

        seqspec = await tools.extract_seqspec(source_text, [source_url])
        stage_results["seqspec"] = seqspec.model_dump(mode="json")
        stage_results["seqspec_json"] = generate_seqspec_json(seqspec)
        stage_results["seqspec_yaml"] = generate_seqspec_yaml(seqspec)

        normalized = seqspec_to_protocol(seqspec)
        normalized_data = normalized.model_dump(mode="json")
        stage_results["normalized"] = normalized_data
        stage_results["formatted"] = format_protocol(normalized).model_dump(mode="json")

        async with async_session() as session:
            await repo.update_ingestion_run(
                session,
                run.id,
                stage="publishing",
                results=stage_results,
            )
            await session.commit()

        publish_result = await tools.publish_protocol(normalized.model_dump_json())
        stage_results["publish_result"] = publish_result

        async with async_session() as session:
            protocol = await repo.get_protocol_by_slug(session, normalized.slug)
            review_request_id = publish_result.get("review_request_id")
            await repo.update_submission(
                session,
                submission_id,
                status=IngestionStatus.COMPLETED.value,
                protocol_id=protocol.id if protocol else None,
                review_request_id=(
                    uuid.UUID(review_request_id) if review_request_id else None
                ),
                error_message=None,
            )
            if protocol is not None:
                await repo.upsert_protocol_seqspec(
                    session,
                    protocol_id=protocol.id,
                    submission_id=submission_id,
                    content_json=seqspec.model_dump(mode="json"),
                    content_yaml=stage_results["seqspec_yaml"],
                )
            await repo.update_ingestion_run(
                session,
                run.id,
                status=IngestionStatus.COMPLETED.value,
                stage="completed",
                results=stage_results,
                completed_at=datetime.utcnow(),
            )
            await session.commit()
            refreshed = await repo.get_submission_by_id(session, submission_id)
            assert refreshed is not None
            return serialize_submission(refreshed)
    except Exception as exc:
        error_message = str(exc)
        async with async_session() as session:
            await repo.update_submission(
                session,
                submission_id,
                status=IngestionStatus.FAILED.value,
                error_message=error_message,
            )
            await repo.update_ingestion_run(
                session,
                run.id,
                status=IngestionStatus.FAILED.value,
                stage="failed",
                results=stage_results,
                errors=[error_message],
                completed_at=datetime.utcnow(),
            )
            await session.commit()
            refreshed = await repo.get_submission_by_id(session, submission_id)
            if refreshed is None:
                raise
            return serialize_submission(refreshed)
