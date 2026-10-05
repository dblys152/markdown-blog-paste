#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="md2blog-505805"
REGION="asia-southeast1"
API_SERVICE="md2blog-api"
API_SERVICE_ACCOUNT="md2blog-api@md2blog-505805.iam.gserviceaccount.com"

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
  "md2blog-r2-access-key-id"
  "md2blog-r2-secret-access-key"
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
  --set-secrets "DATABASE_URL=md2blog-database-url:latest,JWT_SECRET_KEY=md2blog-jwt-secret-key:latest,SMTP_PASSWORD=md2blog-smtp-password:latest,OUTBOX_TOKEN_ENCRYPTION_KEY=md2blog-outbox-token-encryption-key:latest,R2_ACCESS_KEY_ID=md2blog-r2-access-key-id:latest,R2_SECRET_ACCESS_KEY=md2blog-r2-secret-access-key:latest"

echo "Cloud Run Service deployment completed."
