#!/bin/bash

# This script deploys the containerized Flask application to Google Cloud Run.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1" # Must match the region in cloudbuild.yaml and setup_gcp.sh
SERVICE_NAME="notes-app-service"
ARTIFACT_REGISTRY_REPO="notes-app-repo"
IMAGE_NAME="notes-app"
# --------------------

echo "--- Deploying to Google Cloud Run ---"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"

# Build the Docker image (optional, Cloud Build does this automatically)
echo "Building Docker image locally (for testing/manual deployment)..."
docker build -t $IMAGE_NAME ./app

# Tag the image for Artifact Registry
echo "Tagging Docker image for Artifact Registry..."
docker tag $IMAGE_NAME $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:latest

# Push the Docker image to Artifact Registry
echo "Pushing Docker image to Artifact Registry..."
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:latest

# Deploy to Cloud Run
echo "Deploying '$IMAGE_NAME:latest' to Cloud Run service '$SERVICE_NAME'..."
gcloud run deploy $SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO/$IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --update-secrets 'GEMINI_API_KEY=gemini-api-key:latest' \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --service-account "cloud-run-notes-app-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --quiet

echo "--- Deployment to Cloud Run Complete ---"
echo "You can find the Cloud Run service at:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
