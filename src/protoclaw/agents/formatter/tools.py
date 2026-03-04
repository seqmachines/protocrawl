"""Formatter agent tools for rendering protocol outputs."""

from __future__ import annotations

from pydantic import BaseModel

from protoclaw.models.protocol import Protocol, ReadSegment


class FormattedOutput(BaseModel):
    """All formatted outputs for a single protocol."""

    slug: str
    read_diagram: str
    summary: str
    json_output: str


def _segment_label(seg: ReadSegment) -> str:
    """Human-readable label for a read segment."""
    role_names = {
        "cell_barcode": "Cell Barcode",
        "umi": "UMI",
        "cdna": "cDNA",
        "sample_index": "Sample Index",
        "linker": "Linker",
        "spacer": "Spacer",
        "primer": "Primer",
        "adapter": "Adapter",
        "feature_barcode": "Feature Barcode",
        "genomic_insert": "Genomic Insert",
        "other": "Other",
    }
    label = role_names.get(seg.role, seg.role)
    if seg.description:
        label = seg.description
    return label


def _render_read_line(
    segments: list[ReadSegment],
    total_length: int | None,
) -> str:
    """Render a single read as an ASCII diagram line."""
    if not segments:
        if total_length:
            return f"|<{'─' * 20} ({total_length}bp) {'─' * 20}>|"
        return "|< empty >|"

    parts = []
    for seg in sorted(segments, key=lambda s: s.start_pos):
        label = _segment_label(seg)
        length_str = f"{seg.length}bp" if seg.length else "var"
        part = f" {label} ({length_str}) "
        parts.append(part)

    line = "|" + "|".join(parts) + "|"
    return line


_READ_NAMES = {
    1: "Read 1",
    2: "Read 2",
    3: "Index 1 (i7)",
    4: "Index 2 (i5)",
}

_READ_LENGTH_KEYS = {
    1: "read1_length",
    2: "read2_length",
    3: "index1_length",
    4: "index2_length",
}


def render_read_diagram(protocol: Protocol) -> str:
    """Generate an ASCII diagram of the protocol's read structure.

    Args:
        protocol: A normalized Protocol instance.

    Returns:
        Multi-line string with ASCII read structure diagram.
    """
    geom = protocol.read_geometry
    lines = [f"Read Structure: {protocol.name}", ""]

    # Group segments by read number
    by_read: dict[int, list[ReadSegment]] = {}
    for seg in geom.segments:
        by_read.setdefault(seg.read_number, []).append(seg)

    # Determine which reads exist
    read_numbers = sorted(by_read.keys())
    if not read_numbers:
        # Fall back to declared lengths
        for rn in [1, 2, 3, 4]:
            length_attr = _READ_LENGTH_KEYS[rn]
            length = getattr(geom, length_attr, None)
            if length:
                read_numbers.append(rn)

    for rn in read_numbers:
        name = _READ_NAMES.get(rn, f"Read {rn}")
        length_attr = _READ_LENGTH_KEYS.get(rn, "")
        length = getattr(geom, length_attr, None) if length_attr else None
        length_str = f" ({length} bp)" if length else ""

        lines.append(f"{name}{length_str}:")
        segments = by_read.get(rn, [])
        lines.append(_render_read_line(segments, length))
        lines.append("")

    return "\n".join(lines).rstrip()


def generate_summary(protocol: Protocol) -> str:
    """Generate a human-readable summary of the protocol.

    Args:
        protocol: A normalized Protocol instance.

    Returns:
        Multi-paragraph plain-text summary.
    """
    paragraphs = []

    # Paragraph 1: What it is
    vendor_str = f" by {protocol.vendor}" if protocol.vendor else ""
    platform_str = f" for the {protocol.platform} platform" if protocol.platform else ""
    p1 = (
        f"{protocol.name} is a {protocol.assay_family} protocol"
        f"{vendor_str}{platform_str}. {protocol.description}"
    )
    paragraphs.append(p1)

    # Paragraph 2: Technical details
    geom = protocol.read_geometry
    tech_parts = [f"The library uses {geom.read_type} sequencing"]
    if geom.read1_length:
        tech_parts.append(f"Read 1 is {geom.read1_length} bp")
    if geom.read2_length:
        tech_parts.append(f"Read 2 is {geom.read2_length} bp")

    bc_parts = []
    for bc in protocol.barcodes:
        bc_parts.append(f"{bc.length}bp {bc.role}")
    if bc_parts:
        tech_parts.append(f"Barcoding scheme includes: {', '.join(bc_parts)}")

    paragraphs.append(". ".join(tech_parts) + ".")

    # Paragraph 3: Caveats
    if protocol.caveats:
        caveat_text = "Notable considerations: " + "; ".join(protocol.caveats)
        paragraphs.append(caveat_text)

    return "\n\n".join(paragraphs)


def generate_json(protocol: Protocol) -> str:
    """Generate canonical JSON output for the protocol.

    Args:
        protocol: A normalized Protocol instance.

    Returns:
        Pretty-printed JSON string.
    """
    return protocol.model_dump_json(indent=2)


def format_protocol(protocol: Protocol) -> FormattedOutput:
    """Generate all formatted outputs for a protocol.

    Args:
        protocol: A normalized Protocol instance.

    Returns:
        FormattedOutput with read_diagram, summary, and json_output.
    """
    return FormattedOutput(
        slug=protocol.slug,
        read_diagram=render_read_diagram(protocol),
        summary=generate_summary(protocol),
        json_output=generate_json(protocol),
    )
