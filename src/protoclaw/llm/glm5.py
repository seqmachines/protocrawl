"""GLM-5 client via Vertex AI Model Garden (MaaS).

Vertex AI exposes GLM-5 through an OpenAI-compatible endpoint.
Authentication uses Google Application Default Credentials.
"""

import json

from openai import AsyncOpenAI
from pydantic import BaseModel

from protoclaw.config import settings


def _build_base_url() -> str:
    project = settings.gcp_project
    location = settings.gcp_location
    return (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{location}/endpoints/openapi"
    )


def _get_access_token() -> str:
    """Get access token from Application Default Credentials."""
    import google.auth
    import google.auth.transport.requests

    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def get_client() -> AsyncOpenAI:
    """Create an AsyncOpenAI client pointed at Vertex AI MaaS."""
    return AsyncOpenAI(
        base_url=_build_base_url(),
        api_key=_get_access_token(),
    )


async def generate(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int = 8192,
) -> str:
    """Generate text from GLM-5."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=settings.vertex_model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


async def extract_structured(
    prompt: str,
    response_model: type[BaseModel],
    *,
    system: str | None = None,
    max_tokens: int = 8192,
) -> BaseModel:
    """Call GLM-5 and parse the response into a Pydantic model.

    Instructs the model to return JSON matching the schema, then
    validates and returns a Pydantic instance.
    """
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    json_instruction = (
        f"Respond ONLY with valid JSON matching this schema:\n"
        f"```json\n{schema_json}\n```\n"
        f"No markdown, no explanation, just the JSON object."
    )

    full_system = json_instruction
    if system:
        full_system = f"{system}\n\n{json_instruction}"

    raw = await generate(prompt, system=full_system, max_tokens=max_tokens)

    # Strip markdown fences if the model wraps its output
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    return response_model.model_validate_json(cleaned)
