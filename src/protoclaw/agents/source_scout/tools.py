"""Source Scout agent tools for discovering protocol source documents."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import httpx
import yaml

from protoclaw.models.source import SourceDocument


async def load_seed_sources(
    seeds_path: str | None = None,
) -> list[SourceDocument]:
    """Load curated source URLs from the seeds/sources.yaml file.

    Args:
        seeds_path: Path to sources.yaml. Defaults to seeds/sources.yaml
            relative to the project root.

    Returns:
        List of SourceDocument instances from the seed file.
    """
    if seeds_path is None:
        seeds_path = str(
            Path(__file__).parent.parent.parent.parent.parent / "seeds" / "sources.yaml"
        )

    path = Path(seeds_path)
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text())
    sources = data.get("sources", [])

    return [
        SourceDocument(
            url=s["url"],
            title=s.get("title"),
            source_type=s.get("source_type", "unknown"),
        )
        for s in sources
    ]


async def search_arxiv(
    query: str,
    max_results: int = 10,
) -> list[SourceDocument]:
    """Search arXiv for papers matching a query.

    Args:
        query: Search query string (e.g., "single-cell RNA-seq library").
        max_results: Maximum number of results to return.

    Returns:
        List of SourceDocument instances from arXiv search results.
    """
    import arxiv

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    for paper in client.results(search):
        results.append(
            SourceDocument(
                url=paper.entry_id,
                title=paper.title,
                source_type="preprint",
                metadata={
                    "abstract": paper.summary,
                    "authors": [a.name for a in paper.authors],
                    "published": paper.published.isoformat()
                    if paper.published
                    else None,
                    "categories": paper.categories,
                },
                discovered_at=datetime.utcnow(),
            )
        )

    return results


async def search_github(
    query: str,
    max_results: int = 10,
) -> list[SourceDocument]:
    """Search GitHub repositories for protocol-related content.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of SourceDocument instances from GitHub search.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": max_results,
            },
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for repo in data.get("items", []):
        results.append(
            SourceDocument(
                url=repo["html_url"],
                title=repo.get("full_name", ""),
                source_type="github",
                metadata={
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language"),
                    "topics": repo.get("topics", []),
                },
                discovered_at=datetime.utcnow(),
            )
        )

    return results


async def fetch_page_text(
    url: str,
    max_chars: int = 5000,
) -> SourceDocument:
    """Fetch a web page and extract its text content.

    Args:
        url: URL to fetch.
        max_chars: Maximum characters of text to retain.

    Returns:
        SourceDocument with raw_text populated.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        raw_html = response.text

    # Simple HTML-to-text: strip tags
    import re

    text = re.sub(r"<script[^>]*>.*?</script>", "", raw_html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:max_chars]

    content_hash = hashlib.sha256(raw_html.encode()).hexdigest()

    return SourceDocument(
        url=url,
        source_type="vendor_docs",
        raw_text=text,
        content_hash=content_hash,
        fetched_at=datetime.utcnow(),
    )


def get_search_keywords(
    seeds_path: str | None = None,
) -> list[str]:
    """Load search keywords from seeds/sources.yaml.

    Args:
        seeds_path: Path to sources.yaml.

    Returns:
        List of keyword strings for arXiv/GitHub search.
    """
    if seeds_path is None:
        seeds_path = str(
            Path(__file__).parent.parent.parent.parent.parent / "seeds" / "sources.yaml"
        )

    path = Path(seeds_path)
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text())
    return data.get("search_keywords", [])
