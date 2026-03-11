import os
from flask import Flask, request, jsonify
from google.cloud import firestore
from google.cloud import secretmanager

app = Flask(__name__)

# Initialize Firestore DB
db = firestore.Client()
notes_collection = db.collection('notes')

# Initialize Secret Manager client
secret_manager_client = secretmanager.SecretManagerServiceClient()
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

def get_secret(secret_name):
    try:
        if not PROJECT_ID:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_manager_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        app.logger.error(f"Error accessing secret '{secret_name}': {e}")
        return None

@app.route('/')
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/notes', methods=['GET'])
def get_notes():
    try:
        notes = []
        for doc in notes_collection.stream():
            note = doc.to_dict()
            note['id'] = doc.id
            notes.append(note)
        return jsonify(notes), 200
    except Exception as e:
        app.logger.error(f"Error getting notes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/notes', methods=['POST'])
def create_note():
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({"error": "Missing 'title' or 'content' in request"}), 400

        title = data['title']
        content = data['content']
        # Add a timestamp to the note
        note_data = {
            'title': title,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        doc_ref = notes_collection.add(note_data)
        return jsonify({"id": doc_ref.id, "message": "Note created successfully"}), 201
    except Exception as e:
        app.logger.error(f"Error creating note: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This is used when running locally. When deploying to Cloud Run,
    # a webserver process (like Gunicorn) will be used to run the app.
    # The SECRET_GEMINI_API_KEY will be accessed via Secret Manager in Cloud Run.
    # For local testing, you might set it as an environment variable or
    # mock the secret manager call.
    GEMINI_API_KEY = get_secret('gemini-api-key')
    if not GEMINI_API_KEY:
        app.logger.warning("GEMINI_API_KEY not found. Ensure 'gemini-api-key' is in Secret Manager or set locally for testing.")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
