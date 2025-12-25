from flask import Flask, render_template, request, redirect, url_for, current_app
import os
import io
import json
import uuid
import hashlib
import requests
from time import time
from dotenv import load_dotenv
from datetime import datetime

# ===============================
# Environment & API Configuration
# ===============================

# Load environment variables
load_dotenv("/storage/emulated/0/Text_summarizer/.env")

HF_TOKEN = os.getenv('HF_TOKEN')
API_URL = "https://router.huggingface.co/hf-inference/models/google-t5/t5-small"

# Authorization header for Hugging Face API
headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# ===============================
# Cache Configuration
# ===============================

# In-memory cache to avoid repeated API calls
TEMP_CACHE = {}
CACHE_TTL = 300  # Cache lifetime (5 minutes)

# ===============================
# Flask App Initialization
# ===============================

app = Flask(__name__, instance_relative_config=True)

# ===============================
# Utility Helpers
# ===============================

def text_hash(text):
    """
    Generate a stable SHA256 hash for input text.
    Used to identify duplicate summarization requests.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cleanup_cache():
    """
    Remove expired entries from in-memory cache.
    """
    now = time()
    expired_keys = []

    for key, value in TEMP_CACHE.items():
        if now - value["timestamp"] > CACHE_TTL:
            expired_keys.append(key)

    for key in expired_keys:
        del TEMP_CACHE[key]

# ===============================
# Routes
# ===============================

@app.route("/")
def index():
    """Render homepage."""
    return render_template("index.html")


@app.route("/library")
def show_library():
    """
    Display saved summaries from persistent storage.
    """
    json_path = os.path.join(current_app.instance_path, "summaries.json")

    # If no summaries exist yet
    if not os.path.exists(json_path):
        return render_template("save.html", data=[])

    with open(json_path, "r") as f:
        data = json.load(f)

    return render_template("library.html", summaries=data)


@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Generate or retrieve a summary for provided text.
    Cache lookup order:
    1. In-memory cache
    2. Disk-based JSON storage
    3. Hugging Face API
    """
    cleanup_cache()

    text = request.json.get("text")
    if not text:
        return {"error": "No text provided"}, 400

    hash_id = text_hash(text)

    # 1. In-memory cache
    if hash_id in TEMP_CACHE:
        return {
            "summary": TEMP_CACHE[hash_id]["summary"],
            "cached": "memory",
            "hash": hash_id
        }

    json_path = os.path.join(current_app.instance_path, "summaries.json")

    # 2. Persistent JSON cache
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    for item in data:
        if item.get("hash") == hash_id:
            TEMP_CACHE[hash_id] = {
                "summary": item["summary"],
                "timestamp": time()
            }
            return {
                "summary": item["summary"],
                "cached": "disk",
                "hash": hash_id
            }

    # 3. External API call
    payload = {
        "inputs": f"summarize: {text}",
        "parameters": {
            "max_length": 120,
            "min_length": 30
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return {"error": "API request failed"}, 500

    result = response.json()
    summary_text = result[0]["translation_text"]

    # Store result in temporary cache
    TEMP_CACHE[hash_id] = {
        "summary": summary_text,
        "timestamp": time()
    }

    return {
        "summary": summary_text,
        "cached": False,
        "hash": hash_id
    }


@app.route("/save", methods=["POST"])
def save_file():
    """
    Persist a summary to disk if not already saved.
    """
    summary_text = request.json.get("summary")
    hash_id = request.json.get("hash")

    if not summary_text and not hash:
        return {"status": "error"}, 400

    json_path = os.path.join(current_app.instance_path, "summaries.json")

    # Ensure file exists
    if not os.path.exists(json_path):
        with open(json_path, "w") as f:
            json.dump([], f)

    with open(json_path, "r") as f:
        data = json.load(f)

    # Avoid duplicate saves
    for item in data:
        if item.get("hash") == hash_id:
            return {"status": "success"}, 200

    new_entry = {
        "id": str(uuid.uuid4()),
        "hash": hash_id,
        "summary": summary_text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    data.append(new_entry)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "success"}, 200


@app.route("/delete/<string:summary_id>", methods=["DELETE"])
def delete_summary(summary_id):
    """
    Delete a saved summary by its ID.
    """
    json_path = os.path.join(current_app.instance_path, "summaries.json")

    if not os.path.exists(json_path):
        return {"status": "error"}, 400

    with open(json_path, "r") as f:
        data = json.load(f)

    # Filter out deleted summary
    data = [s for s in data if s["id"] != summary_id]

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "success"}, 200


# ===============================
# Run Server
# ===============================

if __name__ == "__main__":
    app.run(debug=True)