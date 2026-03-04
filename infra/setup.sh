#!/usr/bin/env bash
# Quick GCP infrastructure setup using gcloud CLI
# Usage: ./infra/setup.sh <PROJECT_ID> <DB_PASSWORD>

set -euo pipefail

PROJECT_ID="${1:?Usage: $0 <PROJECT_ID> <DB_PASSWORD>}"
DB_PASSWORD="${2:?Usage: $0 <PROJECT_ID> <DB_PASSWORD>}"
REGION="${3:-us-central1}"

echo "==> Setting project to ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

echo "==> Enabling required APIs"
gcloud services enable \
  sqladmin.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com

echo "==> Creating Artifact Registry repository"
gcloud artifacts repositories create protoclaw \
  --repository-format=docker \
  --location="${REGION}" \
  --quiet || true

echo "==> Creating Cloud SQL instance"
gcloud sql instances create protoclaw-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="${REGION}" \
  --quiet || true

echo "==> Creating database and user"
gcloud sql databases create protoclaw \
  --instance=protoclaw-db --quiet || true
gcloud sql users create protoclaw \
  --instance=protoclaw-db \
  --password="${DB_PASSWORD}" --quiet || true

echo "==> Creating GCS bucket"
gcloud storage buckets create "gs://${PROJECT_ID}-protoclaw-artifacts" \
  --location="${REGION}" --quiet || true

echo "==> Creating service account"
gcloud iam service-accounts create protoclaw-api \
  --display-name="Protoclaw API" --quiet || true

SA_EMAIL="protoclaw-api@${PROJECT_ID}.iam.gserviceaccount.com"

for ROLE in roles/cloudsql.client roles/storage.objectAdmin roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" --quiet
done

echo "==> Building and pushing Docker image"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/protoclaw"
gcloud builds submit --tag "${REGISTRY}/api:latest" .

echo "==> Deploying to Cloud Run"
DB_CONN=$(gcloud sql instances describe protoclaw-db --format='value(connectionName)')
gcloud run deploy protoclaw-api \
  --image="${REGISTRY}/api:latest" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --add-cloudsql-instances="${DB_CONN}" \
  --set-env-vars="PROTOCLAW_GCP_PROJECT=${PROJECT_ID},PROTOCLAW_GCP_LOCATION=${REGION},PROTOCLAW_GCS_BUCKET=${PROJECT_ID}-protoclaw-artifacts,PROTOCLAW_DATABASE_URL=postgresql+asyncpg://protoclaw:${DB_PASSWORD}@/protoclaw?host=/cloudsql/${DB_CONN}" \
  --allow-unauthenticated \
  --port=8000 \
  --memory=512Mi \
  --quiet

API_URL=$(gcloud run services describe protoclaw-api --region="${REGION}" --format='value(status.url)')
echo "==> API deployed at: ${API_URL}"

echo "==> Creating Cloud Scheduler job (weekly Source Scout)"
gcloud scheduler jobs create http protoclaw-source-scout \
  --schedule="0 6 * * 1" \
  --time-zone="America/New_York" \
  --uri="${API_URL}/pipeline/run" \
  --http-method=POST \
  --oidc-service-account-email="${SA_EMAIL}" \
  --quiet || true

echo "==> Done! API: ${API_URL}"
