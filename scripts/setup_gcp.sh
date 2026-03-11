#!/bin/bash

# This script sets up the necessary GCP resources for the DevOps Capstone Project.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1" # Choose your desired GCP region
ARTIFACT_REGISTRY_REPO="notes-app-repo"
SERVICE_ACCOUNT_NAME="cloud-run-notes-app-sa" # Service account for Cloud Run
API_GATEWAY_NAME="notes-api-gateway"
GEMINI_SECRET_NAME="gemini-api-key"
# --------------------

echo "--- Starting GCP Project Setup ---"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# 1. Enable necessary GCP APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    iam.googleapis.com \
    secretmanager.googleapis.com \
    apigateway.googleapis.com \
    apigee.googleapis.com \
    cloudresourcemanager.googleapis.com \
    firestore.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudfunctions.googleapis.com \
    eventarc.googleapis.com \
    --project=$PROJECT_ID

echo "APIs enabled."

# 2. Create Artifact Registry repository
echo "Creating Artifact Registry repository: $ARTIFACT_REGISTRY_REPO in $REGION..."
gcloud artifacts repositories create $ARTIFACT_REGISTRY_REPO \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Notes App images" \
    --project=$PROJECT_ID || echo "Repository might already exist."
echo "Artifact Registry repository created/verified."

# 3. Create Firestore Database (if not exists)
# Firestore is usually enabled when firestore.googleapis.com is enabled.
# You might need to manually select a region if this is your first Firestore DB.
echo "Verifying Firestore setup. You might need to initialize Firestore via GCP Console if it's new."
# gcloud firestore databases create --region=$REGION # Uncomment and run manually if needed for initial setup

# 4. Create Service Account for Cloud Run
echo "Creating Cloud Run service account: $SERVICE_ACCOUNT_NAME..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Service Account for Cloud Run Notes App" \
    --project=$PROJECT_ID || echo "Service account might already exist."
echo "Cloud Run service account created/verified."

# Grant necessary roles to the Cloud Run service account
echo "Granting roles to Cloud Run service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user" # Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" # Access secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" # Write logs
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter" # Write metrics
echo "Roles granted to Cloud Run service account."
'
# 5. Create Secret Manager secret for Gemini API key
echo "Creating Secret Manager secret: $GEMINI_SECRET_NAME..."
# Check if secret exists
if ! gcloud secrets describe $GEMINI_SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
    gcloud secrets create $GEMINI_SECRET_NAME \
        --replication-policy="automatic" \
        --project=$PROJECT_ID
    echo "Secret '$GEMINI_SECRET_NAME' created. Please add a secret value using the GCP Console or 'gcloud secrets versions add' command."
    echo "Example: echo 'YOUR_GEMINI_API_KEY' | gcloud secrets versions add $GEMINI_SECRET_NAME --data-file=-"
else
    echo "Secret '$GEMINI_SECRET_NAME' already exists."
fi
'
# Grant Cloud Build service account necessary permissions
echo "Granting Cloud Build service account roles..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUDBUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/run.admin" # For deploying to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/iam.serviceAccountUser" # To act as the Cloud Run service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/artifactregistry.writer" # To push images to Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUDBUILD_SA" \
    --role="roles/secretmanager.secretAccessor" # To access secrets during deployment
echo "Cloud Build service account roles granted."

echo "--- GCP Project Setup Complete ---"
echo "IMPORTANT: Remember to add your actual Gemini API Key to Secret Manager for the secret '$GEMINI_SECRET_NAME'."
echo "You can do this via the GCP Console or by running:"
echo "  echo 'YOUR_ACTUAL_GEMINI_API_KEY' | gcloud secrets versions add $GEMINI_SECRET_NAME --data-file=- --project=$PROJECT_ID"
