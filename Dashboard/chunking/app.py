import os
import io
import requests
import concurrent.futures
from flask import Flask, request, jsonify, send_file
from pydub import AudioSegment

app = Flask(__name__)
SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")

def process_chunk(index, chunk):
    """Exports a single audio chunk to memory and hits the Sarvam API."""
    chunk_io = io.BytesIO()
    # Export as standard WAV to ensure compatibility
    chunk.export(chunk_io, format="wav")
    chunk_io.seek(0)

    files = {
        "file": (f"chunk_{index}.wav", chunk_io, "audio/wav")
    }
    data = {
        "model": "saaras:v3",
        "mode": "transcribe"
    }
    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    try:
        response = requests.post(
            SARVAM_API_URL, 
            headers=headers, 
            files=files, 
            data=data, 
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Error in chunk {index}: {response.text}")
            return index, ""
            
        result = response.json()
        return index, result.get("transcript", result.get("text", "")).strip()
    except Exception as e:
        print(f"Request failed for chunk {index}: {e}")
        return index, ""

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not SARVAM_API_KEY:
        return jsonify({"error": "SARVAM_API_KEY environment variable is not set."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Load the uploaded file directly into Pydub from memory
        file_bytes = file.read()
        audio = AudioSegment.from_file(io.BytesIO(file_bytes))
        
        # Split into 29-second chunks (29000 ms) to safely stay under the 30s limit
        chunk_length_ms = 29000 
        chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        
        # Process chunks concurrently to avoid long browser timeouts
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_chunk, i, chunk) for i, chunk in enumerate(chunks)]
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Sort by index to maintain the chronological order of the spoken text
        results.sort(key=lambda x: x[0])
        
        # Stitch text back together
        full_transcript = " ".join([text for _, text in results if text])
        
        if not full_transcript.strip():
            return jsonify({"error": "Failed to extract text from audio chunks."}), 500
            
        return jsonify({"transcript": full_transcript})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not SARVAM_API_KEY:
        print("WARNING: SARVAM_API_KEY is not set.")
    app.run(debug=True, port=5000)