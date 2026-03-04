# Protoclaw

An agent-native system for building a structured knowledge base of sequencing protocols. Six AI agents work in a sequential pipeline to discover, triage, parse, normalize, format, and publish protocol definitions into a canonical schema.

## Architecture

```
Source Scout → Triage → Parser → Normalizer → Formatter → Publisher
```

| Agent | Role |
|-------|------|
| **Source Scout** | Discovers protocol sources from seed URLs, arXiv, and GitHub |
| **Triage** | Classifies relevance and assigns assay categories |
| **Parser** | Extracts metadata, read structures, barcodes, adapters, reagents |
| **Normalizer** | Assembles parsed data into the canonical Protocol schema with confidence scoring |
| **Formatter** | Generates summaries, read diagrams, and JSON output |
| **Publisher** | Confidence-gated publishing: auto-publish (>=0.85) or route to human review |

Built with:
- **Google ADK** — `SequentialAgent` + `LlmAgent` orchestration
- **GLM-5** via Vertex AI Model Garden (OpenAI-compatible endpoint with ADC auth)
- **FastAPI** — REST API + Jinja2 review UI
- **PostgreSQL** — async via SQLAlchemy 2.0 + asyncpg
- **Pydantic v2** — canonical protocol schema with 20+ fields

## Protocol Schema

Each protocol captures:
- Read geometry (read type, lengths, segment-level layout)
- Barcode specifications (cell barcode, UMI, sample index)
- Adapters, reagent kits, protocol steps
- QC expectations and failure modes
- Citations and source URLs
- Confidence score and review status

## Quickstart

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Google Cloud credentials (for LLM access)

### Setup

```bash
# Clone and install
git clone <repo-url> && cd protoclaw
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env with your GCP project and database URL

# Start PostgreSQL
docker compose up -d

# Run database migrations
alembic upgrade head

# Load seed protocols
protoclaw seed
```

### CLI Commands

```bash
# Load seed protocols into the database
protoclaw seed --seeds-dir seeds/protocols

# List protocols
protoclaw list
protoclaw list --assay scRNA-seq

# Run the full agent pipeline
protoclaw run --dry-run          # Preview sources
protoclaw run                    # Execute pipeline

# Start the API server
protoclaw serve
```

### API Endpoints

```
GET  /health                          Health check
GET  /protocols                       List protocols (filter: ?assay_family=)
GET  /protocols/{slug}                Protocol detail
GET  /protocols/{slug}/read-geometry  Read geometry detail
GET  /protocols/{slug}/versions       Version history
GET  /reviews                         Pending review requests
GET  /reviews/{id}                    Review detail with read diagram
POST /reviews/{id}/decide             Approve or reject a protocol
```

## Seed Protocols

21 curated protocols across 5 assay families:

| Family | Protocols |
|--------|-----------|
| scRNA-seq | 10x Chromium 3'/5', Drop-seq, Smart-seq2, inDrop, PARSE, CEL-Seq2, STRT-seq, SPLiT-seq, 10x Flex |
| scATAC-seq | 10x ATAC, sci-ATAC-seq |
| Spatial | Visium, Visium HD, Slide-seq, MERFISH, 10x Xenium |
| Multiome | 10x Multiome |
| Bulk RNA-seq | TruSeq Stranded mRNA |
| CITE-seq | CITE-seq |

## Development

```bash
# Run tests
pytest tests/unit/ -v

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/protoclaw/
```

## Deployment

Infrastructure configs are in `infra/`:

- **`main.tf`** — Terraform config for Cloud SQL, Cloud Run, GCS, Artifact Registry, IAM
- **`setup.sh`** — gcloud CLI alternative for provisioning

```bash
# Terraform
cd infra
terraform init
terraform plan -var="project_id=your-project" -var="db_password=secret"
terraform apply

# Or gcloud CLI
bash infra/setup.sh
```

The `Dockerfile` is production-ready with multi-stage build, non-root user, and health check.

## Project Structure

```
src/protoclaw/
  agents/             # 6 ADK agents (source_scout, triage, parser, normalizer, formatter, publisher)
    root_agent.py     # SequentialAgent pipeline wiring
  api/                # FastAPI app, routes, templates
  db/                 # SQLAlchemy tables, repositories, migrations
  llm/                # Vertex AI MaaS client (GLM-5)
  models/             # Pydantic models (protocol, review, source, enums)
  config.py           # Pydantic Settings
  cli.py              # Click CLI (seed, serve, run, list)
seeds/
  protocols/          # 21 YAML seed files
  sources.yaml        # Curated source URLs and search keywords
infra/                # Terraform + gcloud deployment configs
tests/unit/           # 61 unit tests
```

## License

See [LICENSE](LICENSE).
