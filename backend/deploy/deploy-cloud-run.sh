#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="md2blog-505805"
REGION="asia-southeast1"
API_SERVICE="md2blog-api"
PURGE_JOB="md2blog-purge-expired-pages"
OUTBOX_JOB="md2blog-process-outbox"
API_SERVICE_ACCOUNT="md2blog-api@md2blog-505805.iam.gserviceaccount.com"
JOB_SERVICE_ACCOUNT="110854299603-compute@developer.gserviceaccount.com"

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${DEPLOY_DIR}/.." && pwd)"
ENV_FILE="${DEPLOY_DIR}/cloud-run.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Cloud Run environment file is missing: ${ENV_FILE}" >&2
  echo "Copy deploy/cloud-run.env.example and enter the production values." >&2
  exit 1
fi

required_secrets=(
  "md2blog-database-url"
  "md2blog-jwt-secret-key"
  "md2blog-smtp-password"
  "md2blog-outbox-token-encryption-key"
)

for secret in "${required_secrets[@]}"; do
  if ! gcloud secrets describe "${secret}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Required Secret Manager secret is missing: ${secret}" >&2
    exit 1
  fi
done

echo "Deploying ${API_SERVICE}..."
gcloud run deploy "${API_SERVICE}" \
  --source "${BACKEND_DIR}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-account "${API_SERVICE_ACCOUNT}" \
  --env-vars-file "${ENV_FILE}" \
  --set-secrets "DATABASE_URL=md2blog-database-url:latest,JWT_SECRET_KEY=md2blog-jwt-secret-key:latest,OUTBOX_TOKEN_ENCRYPTION_KEY=md2blog-outbox-token-encryption-key:latest"

IMAGE_URL="$(
  gcloud run services describe "${API_SERVICE}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format="value(spec.template.spec.containers[0].image)"
)"

if [[ -z "${IMAGE_URL}" ]]; then
  echo "Failed to resolve the deployed image for ${API_SERVICE}." >&2
  exit 1
fi

echo "Deploying ${PURGE_JOB} with ${IMAGE_URL}..."
gcloud run jobs deploy "${PURGE_JOB}" \
  --image "${IMAGE_URL}" \
  --command md2blog-purge-expired-pages \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-account "${JOB_SERVICE_ACCOUNT}" \
  --set-secrets "DATABASE_URL=md2blog-database-url:latest" \
  --tasks 1 \
  --max-retries 1 \
  --task-timeout 5m

echo "Deploying ${OUTBOX_JOB} with ${IMAGE_URL}..."
gcloud run jobs deploy "${OUTBOX_JOB}" \
  --image "${IMAGE_URL}" \
  --command md2blog-process-outbox \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-account "${JOB_SERVICE_ACCOUNT}" \
  --env-vars-file "${ENV_FILE}" \
  --set-secrets "DATABASE_URL=md2blog-database-url:latest,SMTP_PASSWORD=md2blog-smtp-password:latest,OUTBOX_TOKEN_ENCRYPTION_KEY=md2blog-outbox-token-encryption-key:latest" \
  --tasks 1 \
  --max-retries 0 \
  --task-timeout 5m

echo "Cloud Run Service and Jobs are using the same image: ${IMAGE_URL}"
