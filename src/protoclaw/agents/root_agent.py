"""Root agent — wires the full Protoclaw pipeline as a SequentialAgent."""

from google.adk.agents import SequentialAgent

from protoclaw.agents.formatter.agent import formatter_agent
from protoclaw.agents.normalizer.agent import normalizer_agent
from protoclaw.agents.parser.agent import parser_agent
from protoclaw.agents.publisher.agent import publisher_agent
from protoclaw.agents.source_scout.agent import source_scout_agent
from protoclaw.agents.triage.agent import triage_agent

pipeline_agent = SequentialAgent(
    name="ProtoclawPipeline",
    description=(
        "End-to-end sequencing protocol extraction and publishing pipeline. "
        "Discovers sources, triages relevance, parses protocol details, "
        "normalizes into the canonical schema, formats outputs, and "
        "publishes or queues for human review."
    ),
    sub_agents=[
        source_scout_agent,
        triage_agent,
        parser_agent,
        normalizer_agent,
        formatter_agent,
        publisher_agent,
    ],
)
