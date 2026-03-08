"""Review UI routes — server-rendered Jinja2 templates."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from protoclaw.agents.formatter.tools import render_read_diagram
from protoclaw.api.dependencies import get_db
from protoclaw.db import repositories as repo
from protoclaw.services.protocols import row_to_protocol

router = APIRouter()

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


@router.get("", response_class=HTMLResponse)
async def list_reviews(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """List all pending review requests."""
    reviews = await repo.list_pending_reviews(db)
    return templates.TemplateResponse(
        "reviews_list.html",
        {"request": request, "reviews": reviews},
    )


@router.get("/{review_id}", response_class=HTMLResponse)
async def review_detail(
    request: Request,
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Show detail view for a single review request."""
    review = await repo.get_review_by_id(db, review_id)
    if not review:
        return HTMLResponse("Review not found", status_code=404)

    protocol_row = await repo.get_protocol_by_id(db, review.protocol_id)
    if not protocol_row:
        return HTMLResponse("Protocol not found", status_code=404)

    protocol = row_to_protocol(protocol_row)
    diagram = render_read_diagram(protocol)

    return templates.TemplateResponse(
        "review_detail.html",
        {
            "request": request,
            "review": review,
            "protocol": protocol,
            "read_diagram": diagram,
        },
    )


@router.post("/{review_id}/decide")
async def decide_review(
    review_id: uuid.UUID,
    decision: str = Form(...),
    comments: str = Form(""),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Process a reviewer's decision (approve or reject)."""
    publish = decision == "approved"
    await repo.update_review_status(
        db,
        review_id,
        decision,
        protocol_published=publish,
    )
    await db.commit()
    return RedirectResponse(url="/reviews", status_code=303)
