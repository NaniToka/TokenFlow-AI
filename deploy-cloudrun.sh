#!/bin/bash
set -e

# Google Cloud Run Deployment Script for TokenFlow AI
# Make executable: chmod +x deploy-cloudrun.sh

PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION=${2:-"us-central1"}
SERVICE_NAME="tokenflow-ai"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP Project ID is required."
  echo "Usage: ./deploy-cloudrun.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "🚀 Starting Google Cloud Run deployment for TokenFlow AI..."
echo "  - Project ID: ${PROJECT_ID}"
echo "  - Region:     ${REGION}"
echo "  - Image Tag:  ${IMAGE_NAME}"

# 1. Set gcloud project
gcloud config set project "${PROJECT_ID}"

# 2. Enable necessary GCP APIs
echo "📦 Enabling GCP Service APIs (Cloud Run, Container Registry, Cloud Build)..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# 3. Submit build using Google Cloud Build
echo "🔨 Building Docker image using Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" .

# 4. Deploy container image to Cloud Run
echo "☁️ Deploying container to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "ALLOWED_ORIGINS=*,ENVIRONMENT=production"

echo "✅ Deployment completed successfully!"
echo "To configure your GEMINI_API_KEY on Cloud Run, run:"
echo "  gcloud run services update ${SERVICE_NAME} --set-env-vars GEMINI_API_KEY=your_gemini_api_key_here --region ${REGION}"
