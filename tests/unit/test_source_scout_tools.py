"""Tests for source scout tools."""

from pathlib import Path

import pytest

from protoclaw.agents.source_scout.tools import (
    get_search_keywords,
    load_seed_sources,
)

SEEDS_DIR = Path(__file__).parent.parent.parent / "seeds"


@pytest.mark.asyncio
async def test_load_seed_sources():
    sources = await load_seed_sources(str(SEEDS_DIR / "sources.yaml"))
    assert len(sources) > 0
    assert all(s.url for s in sources)
    assert all(s.source_type for s in sources)

    # Check we have a mix of source types
    types = {s.source_type for s in sources}
    assert "vendor_docs" in types
    assert "paper" in types


@pytest.mark.asyncio
async def test_load_seed_sources_missing_file():
    sources = await load_seed_sources("/nonexistent/path.yaml")
    assert sources == []


def test_get_search_keywords():
    keywords = get_search_keywords(str(SEEDS_DIR / "sources.yaml"))
    assert len(keywords) > 0
    assert any("RNA-seq" in kw for kw in keywords)


def test_get_search_keywords_missing_file():
    keywords = get_search_keywords("/nonexistent/path.yaml")
    assert keywords == []


@pytest.mark.asyncio
async def test_load_seed_sources_has_expected_entries():
    sources = await load_seed_sources(str(SEEDS_DIR / "sources.yaml"))
    urls = {s.url for s in sources}
    # Check a few known seed URLs are present
    assert any("teichlab" in u for u in urls)
    assert any("10xgenomics" in u for u in urls)
    assert any("mccarrolllab" in u for u in urls)
