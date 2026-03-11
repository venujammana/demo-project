from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import google.generativeai as genai

app = Flask(__name__)

# --- Configuration ---
# Set the project ID dynamically based on the environment or Fallback to a placeholder
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
FIRESTORE_COLLECTION = "notes"
GEMINI_API_KEY_SECRET_NAME = "projects/{}/secrets/gemini-api-key/versions/latest".format(PROJECT_ID)

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

# --- Gemini API Initialization ---
# For local development, set GEMINI_API_KEY env var directly.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
else:
    print("Warning: Gemini API Key not found. Gemini integration will be disabled.")
    gemini_model = None


# --- Flask Routes ---

@app.route('/')
def index():
    notes = []
    if db:
        notes_ref = db.collection(FIRESTORE_COLLECTION)
        notes = [doc.to_dict() for doc in notes_ref.stream()]
        # Add 'id' to each note for easier reference in templates
        for note in notes:
            if 'id' not in note:
                note['id'] = notes_ref.document(note['title']).id # Assuming title can be a semi-unique ID for demo
    return render_template('index.html', notes=notes)

@app.route('/notes', methods=['GET'])
def get_notes():
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500
    notes_ref = db.collection(FIRESTORE_COLLECTION)
    notes = []
    for doc in notes_ref.stream():
        note_data = doc.to_dict()
        note_data['id'] = doc.id
        notes.append(note_data)
    return jsonify(notes), 200

@app.route('/notes', methods=['POST'])
def create_note():
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    try:
        doc_ref = db.collection(FIRESTORE_COLLECTION).add({'title': title, 'content': content})
        return jsonify({"message": "Note created", "id": doc_ref[1].id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500
    try:
        doc = db.collection(FIRESTORE_COLLECTION).document(note_id).get()
        if doc.exists:
            note_data = doc.to_dict()
            note_data['id'] = doc.id
            return jsonify(note_data), 200
        else:
            return jsonify({"error": "Note not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(note_id)
        doc_ref.update(data)
        return jsonify({"message": "Note updated", "id": note_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500
    try:
        db.collection(FIRESTORE_COLLECTION).document(note_id).delete()
        return jsonify({"message": "Note deleted", "id": note_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gemini-process-note', methods=['POST'])
def gemini_process_note():
    if not gemini_model:
        return jsonify({"error": "Gemini API not configured. Check GEMINI_API_KEY."}), 500

    data = request.get_json()
    note_content = data.get('content')
    if not note_content:
        return jsonify({"error": "Note content is required for processing"}), 400

    try:
        prompt = f"Summarize the following note in one concise sentence: '{note_content}'"
        response = gemini_model.generate_content(prompt)
        summary = response.text
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {e}"}), 500

# Critical access point example: Admin function accessible only via API Gateway with specific auth
@app.route('/admin/critical-action', methods=['POST'])
def critical_action():
    # In a real application, this endpoint would be protected by API Gateway authentication/authorization
    # e.g., requiring a specific API key, JWT token, or user role.
    # For this demo, we'll return a simple message, assuming API Gateway handles actual access control.
    print("Critical action attempted.")
    return jsonify({"message": "Critical action performed successfully (via protected endpoint)"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
