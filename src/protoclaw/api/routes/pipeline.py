from fastapi import APIRouter, Query

from protoclaw.agents.source_scout.tools import load_seed_sources
from protoclaw.services.ingestion import create_submission_and_ingest

router = APIRouter()


@router.post("/run")
async def run_pipeline(
    dry_run: bool = Query(False),
    limit: int = Query(10, ge=1, le=100),
    seeds_path: str = Query("seeds/sources.yaml"),
    submitted_by: str = Query("scheduler"),
) -> dict:
    sources = await load_seed_sources(seeds_path)
    selected = sources[:limit]

    if dry_run:
        return {
            "count": len(selected),
            "sources": [source.url for source in selected],
        }

    results = []
    for source in selected:
        results.append(
            await create_submission_and_ingest(
                source.url,
                notes=f"Seed source from {seeds_path}",
                submitted_by=submitted_by,
            )
        )

    return {
        "count": len(results),
        "submissions": results,
    }
