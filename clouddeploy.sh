#!/usr/bin/env bash
# Deploy RAG service to Google Cloud Run
# Usage: export required env vars (PROJECT_ID, DB_NAME, DB_USER, DB_HOST, DB_PORT, IMAGE_NAME optional)
# Or place them in a .env file in the same directory
# Then run: ./clouddeploy.sh
set -euo pipefail

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "[INFO] Loading environment variables from .env file..."
  set -a  # automatically export all variables
  source .env
  set +a  # stop automatically exporting
else
  echo "[WARN] No .env file found. Using environment variables or defaults."
fi

# --- Config (override by exporting before running) ---
PROJECT_ID="${PROJECT_ID:-dbdiver}"
REGION="${REGION:-us-central1}"
IMAGE_NAME="${IMAGE_NAME:-dbdiver}"
SERVICE_NAME="${SERVICE_NAME:-dbdiver}"
GCR_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}"

echo "[INFO] Project: $PROJECT_ID"
echo "[INFO] Region: $REGION"
echo "[INFO] Service name: $SERVICE_NAME"
echo "[INFO] Image: $GCR_IMAGE"

# Ensure gcloud is logged in and project set
if ! gcloud config get-value project >/dev/null 2>&1 || [ "$(gcloud config get-value project)" != "$PROJECT_ID" ]; then
  echo "[INFO] Setting gcloud project to $PROJECT_ID"
  gcloud config set project "$PROJECT_ID"
fi

echo "[INFO] Authenticating Docker for GCR..."
gcloud auth configure-docker --quiet

# Enable required APIs
echo "[INFO] Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build & push image
if command -v gcloud >/dev/null 2>&1; then
  echo "[INFO] Building and pushing using Cloud Build..."
  # Try with explicit source flag first
  if ! gcloud builds submit --tag "${GCR_IMAGE}" . 2>/dev/null; then
    echo "[WARN] Cloud Build failed, trying with local Docker build..."
    # Fallback to local build
    docker build -t "${IMAGE_NAME}" .
    docker tag "${IMAGE_NAME}" "${GCR_IMAGE}"
    docker push "${GCR_IMAGE}"
  fi
else
  echo "[INFO] Building locally..."
  docker build -t "${IMAGE_NAME}" .
  docker tag "${IMAGE_NAME}" "${GCR_IMAGE}"
  docker push "${GCR_IMAGE}"
fi

# Create secrets in Secret Manager if env provided
create_secret_if_missing() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ]; then
    echo "[WARN] No value provided for secret $name. Skipping creation."
    return
  fi

  if ! gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "[INFO] Creating secret: $name"
    echo -n "$value" | gcloud secrets create "$name" --data-file=- --project "$PROJECT_ID" --replication-policy="automatic"
  else
    echo "[INFO] Secret exists: $name"
  fi
}

# Create secrets for sensitive values
if [ -n "${DB_PASSWORD:-}" ]; then
  create_secret_if_missing "db-password" "$DB_PASSWORD"
fi
if [ -n "${GEMINI_API_KEY:-}" ]; then
  create_secret_if_missing "gemini-api-key" "$GEMINI_API_KEY"
fi
if [ -n "${FLASK_SECRET_KEY:-}" ]; then
  create_secret_if_missing "flask-secret-key" "$FLASK_SECRET_KEY"
fi

# Prepare env var mappings for deployment (only include non-empty values)
ENV_VARS=()
[ -n "${DB_NAME:-}" ] && ENV_VARS+=("DB_NAME=${DB_NAME}")
[ -n "${DB_USER:-}" ] && ENV_VARS+=("DB_USER=${DB_USER}")
[ -n "${DB_HOST:-}" ] && ENV_VARS+=("DB_HOST=${DB_HOST}")
[ -n "${DB_PORT:-}" ] && ENV_VARS+=("DB_PORT=${DB_PORT}")
[ -n "${PDF_PATH:-}" ] && ENV_VARS+=("PDF_PATH=${PDF_PATH}")
[ -n "${NODE_ENV:-}" ] && ENV_VARS+=("NODE_ENV=${NODE_ENV}")

# Add any other environment variables you want to pass through
[ -n "${DEBUG:-}" ] && ENV_VARS+=("DEBUG=${DEBUG}")
[ -n "${LOG_LEVEL:-}" ] && ENV_VARS+=("LOG_LEVEL=${LOG_LEVEL}")

# Join env vars into comma separated string (only if we have any)
if [ ${#ENV_VARS[@]} -gt 0 ]; then
  ENV_VARS_CSV="$(IFS=, ; echo "${ENV_VARS[*]}")"
  echo "[INFO] Environment variables to deploy: $ENV_VARS_CSV"
else
  ENV_VARS_CSV=""
  echo "[WARN] No environment variables to deploy"
fi

# Prepare --update-secrets args (only include secrets that exist)
SECRETS_ARGS=()
if gcloud secrets describe db-password --project "$PROJECT_ID" >/dev/null 2>&1; then
  SECRETS_ARGS+=(--update-secrets "DB_PASSWORD=db-password:latest")
fi
if gcloud secrets describe gemini-api-key --project "$PROJECT_ID" >/dev/null 2>&1; then
  SECRETS_ARGS+=(--update-secrets "GEMINI_API_KEY=gemini-api-key:latest")
fi
if gcloud secrets describe flask-secret-key --project "$PROJECT_ID" >/dev/null 2>&1; then
  SECRETS_ARGS+=(--update-secrets "FLASK_SECRET_KEY=flask-secret-key:latest")
fi

echo "[INFO] Deploying to Cloud Run..."
# Deploy with proper environment variables
DEPLOY_CMD=(
  gcloud run deploy "$SERVICE_NAME"
  --image "$GCR_IMAGE"
  --platform managed
  --region "$REGION"
  --allow-unauthenticated
  --concurrency 80
  --timeout 300
  --memory 2Gi
  --cpu 1
)

# Add environment variables if we have any
if [ -n "$ENV_VARS_CSV" ]; then
  DEPLOY_CMD+=(--set-env-vars "$ENV_VARS_CSV")
fi

# Add secrets if we have any
if [ ${#SECRETS_ARGS[@]} -gt 0 ]; then
  DEPLOY_CMD+=("${SECRETS_ARGS[@]}")
fi

# Execute the deployment
"${DEPLOY_CMD[@]}"

echo "[INFO] Deployment complete. Service: $SERVICE_NAME"
echo "[INFO] Service URL: https://${REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/${PROJECT_ID}/services/${SERVICE_NAME}"