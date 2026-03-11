# DevOps Capstone Project: Containerized Flask Notes Application

This project demonstrates a complete DevOps pipeline for a containerized Python Flask notes application. It utilizes Google Cloud Platform (GCP) services for everything from development to deployment, monitoring, and security.

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Architecture](#architecture)
3.  [Prerequisites](#prerequisites)
4.  [Local Development](#local-development)
5.  [GCP Setup](#gcp-setup)
6.  [Containerization](#containerization)
7.  [CI/CD with Cloud Build](#ci/cd-with-cloud-build)
8.  [Cloud Run Deployment](#cloud-run-deployment)
9.  [API Gateway Configuration](#api-gateway-configuration)
10. [Firestore Database](#firestore-database)
11. [Monitoring with Cloud Monitoring](#monitoring-with-cloud-monitoring)
12. [Logging with Cloud Logging](#logging-with-cloud-logging)
13. [Alerting and Notifications](#alerting-and-notifications)
14. [API Endpoints](#api-endpoints)
15. [Security Considerations](#security-considerations)
16. [Cleanup](#cleanup)

## 1. Project Overview

This project implements a simple Flask-based "notes" application that allows users to create and retrieve notes. The application is containerized using Docker and deployed to Google Cloud Run. A CI/CD pipeline with Cloud Build automates the build and deployment process. API Gateway is used to expose the application's API, and Firestore serves as the backend database. Google Secret Manager is used to securely store sensitive information like the Gemini API key. Monitoring, logging, and alerting are integrated using Cloud Monitoring and Cloud Logging.

## 2. Architecture

The application follows a modern serverless architecture on GCP:

```
[Client (e.g., Web App, Postman)]
        |
        v
[API Gateway]
        | (Routes requests)
        v
[Cloud Run Service] (Containerized Flask Application)
        |
        v
[Firestore Database] (Stores notes data)
        |
        v
[Secret Manager] (Retrieves Gemini API Key for Flask App)
        ^
        |
[Cloud Logging / Monitoring] (Collects logs and metrics from Cloud Run)
```

## 3. Prerequisites

Before you begin, ensure you have the following:

*   **Google Cloud Platform (GCP) Project:** A GCP project with billing enabled.
*   **`gcloud` CLI:** The Google Cloud SDK installed and configured.
    *   `gcloud auth login`
    *   `gcloud config set project YOUR_PROJECT_ID`
*   **Docker:** Docker Desktop or Docker Engine installed.
*   **Python 3.9+:** Python installed locally (for local development).
*   **`pip`:** Python package installer.

## 4. Local Development

You can run the Flask application locally for testing:

1.  Navigate to the `app` directory:
    ```bash
    cd demo-project/app
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up Firestore locally (optional, for full local testing):
    *   You would typically use a Firestore emulator or mock the Firestore calls for local development without connecting to a live Firestore.
    *   For simplicity in this demo, the local `main.py` will attempt to connect to a live Firestore. Ensure your `gcloud` is authenticated to a project with Firestore enabled.
4.  Set the `GOOGLE_CLOUD_PROJECT` environment variable (required by the app to connect to Secret Manager):
    ```bash
    export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
    ```
5.  Run the application:
    ```bash
    python main.py
    ```
    The application should be accessible at `http://127.0.0.1:8080`.

## 5. GCP Setup

The `scripts/setup_gcp.sh` script automates the initial configuration of your GCP project.

1.  Navigate to the project root:
    ```bash
    cd demo-project
    ```
2.  Make the setup script executable:
    ```bash
    chmod +x scripts/setup_gcp.sh
    ```
3.  Run the setup script:
    ```bash
    ./scripts/setup_gcp.sh
    ```
    This script will:
    *   Enable necessary GCP APIs (Artifact Registry, Cloud Build, Cloud Run, Secret Manager, API Gateway, Firestore, Logging, Monitoring).
    *   Create an Artifact Registry Docker repository (`notes-app-repo`).
    *   Create a dedicated service account for Cloud Run (`cloud-run-notes-app-sa`) and grant it the necessary IAM roles (Firestore access, Secret Manager accessor, Log Writer, Metric Writer).
    *   Create a Secret Manager secret named `gemini-api-key`.
    *   Grant Cloud Build the necessary permissions to deploy to Cloud Run, push to Artifact Registry, and access secrets.

4.  **IMPORTANT: Add your Gemini API Key to Secret Manager:**
    After running the setup script, you MUST add your actual Gemini API Key to the Secret Manager secret `gemini-api-key`.
    ```bash
    echo 'YOUR_ACTUAL_GEMINI_API_KEY' | gcloud secrets versions add gemini-api-key --data-file=- --project=YOUR_PROJECT_ID
    ```
    Replace `YOUR_ACTUAL_GEMINI_API_KEY` with your real key.

## 6. Containerization

The application is containerized using Docker. The `app/Dockerfile` defines the image build process.

To build the Docker image locally:
```bash
cd demo-project
docker build -t notes-app-image ./app
```

To push the image to Artifact Registry (manual push, usually handled by Cloud Build):
```bash
# First, authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag your image
docker tag notes-app-image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/notes-app-repo/notes-app:latest

# Push the image
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/notes-app-repo/notes-app:latest
```

## 7. CI/CD with Cloud Build

The `cloudbuild.yaml` file defines the CI/CD pipeline using Google Cloud Build.

### How it works:

1.  **Build Step:** Uses `gcr.io/cloud-builders/docker` to build the Docker image from `app/Dockerfile`. The image is tagged with the `COMMIT_SHA` for versioning.
2.  **Push Step:** Pushes the built Docker image to the Artifact Registry repository.
3.  **Deploy Step:** Deploys the new Docker image to a Cloud Run service named `notes-app-service`. It also mounts the `gemini-api-key` from Secret Manager and sets the `GOOGLE_CLOUD_PROJECT` environment variable.

### Setting up a Cloud Build Trigger:

To automate the CI/CD pipeline, you can create a Cloud Build trigger that listens for changes in your Git repository (e.g., pushes to the `main` branch).

1.  **Connect your repository:** Go to **Cloud Build -> Triggers** in the GCP Console.
2.  Click **"Create trigger"**.
3.  Configure the trigger:
    *   **Name:** e.g., `notes-app-ci-cd`
    *   **Region:** Global or your preferred region.
    *   **Event:** `Push to a branch`
    *   **Source:** Select your repository (e.g., GitHub, Cloud Source Repositories).
    *   **Branch:** e.g., `^main$`
    *   **Build configuration:** `Cloud Build configuration file`
    *   **Cloud Build file location:** `demo-project/cloudbuild.yaml`
    *   **Substitutions:** You might need to add `_SERVICE_ACCOUNT_NAME=cloud-run-notes-app-sa` if your `cloudbuild.yaml` explicitly references it. (The current `cloudbuild.yaml` uses the default Cloud Run service account but can be modified).

Now, every time you push changes to the specified branch, Cloud Build will automatically build, push, and deploy your application.

## 8. Cloud Run Deployment

The application is deployed as a serverless container to Google Cloud Run. Cloud Run automatically scales your container up and down based on traffic.

### Manual Deployment (using `deploy.sh`):

The `scripts/deploy.sh` script provides a convenient way to manually build, push, and deploy the application to Cloud Run.

1.  Navigate to the project root:
    ```bash
    cd demo-project
    ```
2.  Make the deployment script executable:
    ```bash
    chmod +x scripts/deploy.sh
    ```
3.  Run the deployment script:
    ```bash
    ./scripts/deploy.sh
    ```
    This script will perform the Docker build, push the image to Artifact Registry, and deploy it to Cloud Run.

After deployment, you can find the Cloud Run service URL in the output of the script or by navigating to **Cloud Run -> notes-app-service** in the GCP Console.

## 9. API Gateway Configuration

API Gateway is used to provide a single, consistent entry point to your Cloud Run service and can add features like authentication, rate limiting, and analytics.

1.  **Get your Cloud Run Service URL:**
    ```bash
    gcloud run services describe notes-app-service --region us-central1 --format="value(status.url)"
    ```
    Copy this URL (e.g., `https://notes-app-service-YOUR_HASH-REGION.a.run.app`).

2.  **Update `api_config.yaml`:**
    Open `demo-project/api_config.yaml` and replace `"CLOUD_RUN_SERVICE_URL"` with the actual URL of your Cloud Run service for both `x-google-backend` entries.

3.  **Create an API Configuration:**
    ```bash
    cd demo-project
    gcloud api-gateway api-configs create notes-app-config \
        --api=notes-api-gateway \
        --openapi-spec=api_config.yaml \
        --project=YOUR_PROJECT_ID \
        --backend-auth-service-account="cloud-run-notes-app-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"
    ```
    *   `--api=notes-api-gateway`: This is the name of the API Gateway resource. If it doesn't exist, it will be created.
    *   `--backend-auth-service-account`: This is crucial for securing the connection between API Gateway and Cloud Run. API Gateway will use this service account to authenticate with your Cloud Run service. Ensure this service account has the `roles/run.invoker` role on the Cloud Run service.

    *Note: The `setup_gcp.sh` script does not create the API Gateway itself. You need to create the API Gateway instance first, then deploy the config.*
    *To create the API Gateway resource:*
    ```bash
    gcloud api-gateway apis create notes-api-gateway --project=YOUR_PROJECT_ID
    ```

4.  **Deploy to a Gateway:**
    ```bash
    gcloud api-gateway gateways create notes-app-gateway \
        --api=notes-api-gateway \
        --api-config=notes-app-config \
        --location=us-central1 \
        --project=YOUR_PROJECT_ID
    ```
    After deployment, the output will provide the URL of your API Gateway.

## 10. Firestore Database

The Flask application uses Google Firestore in Native mode to store notes.

*   You can view your Firestore database and its collections (e.g., `notes`) in the GCP Console: **Firestore -> Data**.
*   The application automatically creates the `notes` collection and adds documents when you make `POST` requests.

## 11. Monitoring with Cloud Monitoring

Cloud Run services automatically integrate with Cloud Monitoring, providing out-of-the-box metrics and dashboards.

1.  Navigate to **Cloud Monitoring -> Dashboards** in the GCP Console.
2.  You can find pre-built dashboards for Cloud Run that show metrics like:
    *   Request count
    *   Latency
    *   Error rates
    *   Container instance count
    *   CPU and Memory utilization
3.  You can also create custom dashboards to visualize specific metrics important to your application.

## 12. Logging with Cloud Logging

Cloud Run automatically sends all container logs (stdout/stderr) to Cloud Logging.

1.  Navigate to **Cloud Logging -> Logs Explorer** in the GCP Console.
2.  Filter logs by:
    *   **Resource Type:** `Cloud Run Revision`
    *   **Service Name:** `notes-app-service`
3.  You will see application logs generated by `main.py` (e.g., error messages, request information).

## 13. Alerting and Notifications

You can set up alerting policies in Cloud Monitoring to notify you of critical events or performance issues.

1.  Navigate to **Cloud Monitoring -> Alerting** in the GCP Console.
2.  Click **"Create Policy"**.
3.  Define an alert condition, for example:
    *   **Target:** Select `Cloud Run Revision`, then your `notes-app-service`.
    *   **Metric:** e.g., `Request count`, `Request latencies`, `Error ratio`.
    *   **Condition:** e.g., `Error ratio > 0.05` for 5 minutes.
4.  Configure notification channels (e.g., email, PagerDuty, Slack).

## 14. API Endpoints

Once your API Gateway is deployed, you can interact with the notes application using its public URL.

*   **API Gateway URL:** Obtain this from the output of the `gcloud api-gateway gateways create` command.

### GET /notes

Retrieves all notes stored in Firestore.

```bash
curl -X GET "YOUR_API_GATEWAY_URL/notes"
```

Example Response:
```json
[
  {
    "id": "some-firestore-doc-id-1",
    "title": "My First Note",
    "content": "This is the content of my first note.",
    "timestamp": "2023-10-27T10:00:00Z"
  },
  {
    "id": "some-firestore-doc-id-2",
    "title": "Shopping List",
    "content": "Milk, Eggs, Bread",
    "timestamp": "2023-10-27T10:05:00Z"
  }
]
```

### POST /notes

Creates a new note.

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"title": "New Idea", "content": "Brainstorming for a new project."}' \
     "YOUR_API_GATEWAY_URL/notes"
```

Example Response:
```json
{
  "id": "some-new-firestore-doc-id",
  "message": "Note created successfully"
}
```

## 15. Security Considerations

*   **Service Accounts:** The use of dedicated service accounts (`cloud-run-notes-app-sa` for Cloud Run, Cloud Build default SA for CI/CD) with minimal necessary IAM roles (Principle of Least Privilege) enhances security.
*   **Secret Manager:** Sensitive data like API keys are stored securely in Secret Manager and injected into Cloud Run as environment variables, avoiding hardcoding them in code or Docker images.
*   **API Gateway Authentication:** While this demo uses `--allow-unauthenticated` for Cloud Run and relies on API Gateway for public access, in a production scenario, you would secure API Gateway itself (e.g., with API keys, Firebase Authentication, or Auth0) and remove `--allow-unauthenticated` from Cloud Run, granting `roles/run.invoker` to the API Gateway service account.
*   **Firestore Security Rules:** For a real application, you must configure Firestore Security Rules to control access to your data, preventing unauthorized read/write operations directly to the database.

## 16. Cleanup

To avoid incurring unwanted charges, you can clean up the GCP resources created by this project.

1.  **Delete Cloud Run Service:**
    ```bash
    gcloud run services delete notes-app-service --region us-central1 --project=YOUR_PROJECT_ID
    ```

2.  **Delete API Gateway and API Config:**
    ```bash
    gcloud api-gateway gateways delete notes-app-gateway --location us-central1 --project=YOUR_PROJECT_ID
    gcloud api-gateway api-configs delete notes-app-config --api=notes-api-gateway --project=YOUR_PROJECT_ID
    gcloud api-gateway apis delete notes-api-gateway --project=YOUR_PROJECT_ID
    ```

3.  **Delete Artifact Registry Repository:**
    ```bash
    gcloud artifacts repositories delete notes-app-repo --location us-central1 --project=YOUR_PROJECT_ID
    ```

4.  **Delete Secret Manager Secret:**
    ```bash
    gcloud secrets delete gemini-api-key --project=YOUR_PROJECT_ID
    ```

5.  **Delete Firestore Collection (optional):**
    You can delete the `notes` collection directly from the GCP Console (Firestore -> Data) or use the `gcloud firestore delete --collection-id=notes` command (be careful, this is irreversible).

6.  **Delete Service Account:**
    ```bash
    gcloud iam service-accounts delete "cloud-run-notes-app-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" --project=YOUR_PROJECT_ID
    ```

7.  **Disable APIs (optional):**
    You can disable the APIs that were enabled, but this might affect other services in your project.

8.  **Delete the entire GCP Project (DANGER!):**
    If this project was created specifically for this demo and contains no other resources, you can delete the entire GCP project. **This is irreversible and will delete ALL resources within the project.**
    ```bash
    gcloud projects delete YOUR_PROJECT_ID
    ```
