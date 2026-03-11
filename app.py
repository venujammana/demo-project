from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os


app = Flask(__name__)

# --- Configuration ---
# Set the project ID dynamically based on the environment or Fallback to a placeholder
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
FIRESTORE_COLLECTION = "notes"


# --- Firestore Initialization ---
# For Cloud Run, Application Default Credentials will be used.
# For local development, GOOGLE_APPLICATION_CREDENTIALS env var pointing to a service account key is expected.
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
    db = firestore.client()
    print(f"Firestore initialized for project: {PROJECT_ID}")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    print("Ensure 'GOOGLE_APPLICATION_CREDENTIALS' is set for local development, or running in GCP environment.")
    db = None # Set db to None if initialization fails


