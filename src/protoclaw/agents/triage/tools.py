"""Triage agent tools for evaluating source document relevance."""

from pydantic import BaseModel, Field

from protoclaw.llm import glm5
from protoclaw.models.enums import AssayFamily


class RelevanceResult(BaseModel):
    """Result of relevance classification."""

    score: float = Field(ge=0.0, le=1.0)
    reason: str
    is_relevant: bool = Field(description="True if score >= 0.5 and worth parsing")


class CategoryResult(BaseModel):
    """Result of assay category assignment."""

    assay_family: AssayFamily
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class TriageResult(BaseModel):
    """Combined triage output for a single source document."""

    relevance: RelevanceResult
    category: CategoryResult | None = None
    should_parse: bool


_TRIAGE_SYSTEM = (
    "You are an expert in sequencing technologies and library preparation. "
    "Evaluate whether source documents describe sequencing protocols that "
    "are worth extracting into a structured knowledge base."
)


async def classify_relevance(
    title: str,
    abstract_or_snippet: str,
    source_type: str = "unknown",
) -> RelevanceResult:
    """Classify whether a source document is relevant to sequencing protocols.

    Args:
        title: Document title or heading.
        abstract_or_snippet: Abstract, summary, or first ~500 words.
        source_type: One of paper, github, vendor_docs, preprint, lab_page.

    Returns:
        RelevanceResult with score, reason, and is_relevant flag.
    """
    prompt = (
        f"Evaluate this {source_type} document for relevance to "
        f"sequencing library preparation protocols.\n\n"
        f"Title: {title}\n\n"
        f"Content:\n{abstract_or_snippet}\n\n"
        f"Score relevance from 0.0 (not relevant) to 1.0 "
        f"(directly describes a protocol with technical details). "
        f"Set is_relevant=true if score >= 0.5."
    )
    return await glm5.extract_structured(
        prompt=prompt,
        response_model=RelevanceResult,
        system=_TRIAGE_SYSTEM,
    )


async def assign_category(
    title: str,
    abstract_or_snippet: str,
) -> CategoryResult:
    """Assign an assay family category to a relevant source document.

    Args:
        title: Document title or heading.
        abstract_or_snippet: Abstract, summary, or first ~500 words.

    Returns:
        CategoryResult with assay_family, confidence, and reasoning.
    """
    families = ", ".join(f.value for f in AssayFamily)
    prompt = (
        f"Categorize this sequencing protocol into one of these "
        f"assay families: {families}\n\n"
        f"Title: {title}\n\n"
        f"Content:\n{abstract_or_snippet}"
    )
    return await glm5.extract_structured(
        prompt=prompt,
        response_model=CategoryResult,
        system=_TRIAGE_SYSTEM,
    )


async def triage_source(
    title: str,
    abstract_or_snippet: str,
    source_type: str = "unknown",
) -> TriageResult:
    """Full triage: classify relevance and assign category if relevant.

    Args:
        title: Document title or heading.
        abstract_or_snippet: Abstract, summary, or first ~500 words.
        source_type: One of paper, github, vendor_docs, preprint, lab_page.

    Returns:
        TriageResult with relevance, optional category, and should_parse flag.
    """
    relevance = await classify_relevance(title, abstract_or_snippet, source_type)

    category = None
    if relevance.is_relevant:
        category = await assign_category(title, abstract_or_snippet)

    return TriageResult(
        relevance=relevance,
        category=category,
        should_parse=relevance.is_relevant,
    )
