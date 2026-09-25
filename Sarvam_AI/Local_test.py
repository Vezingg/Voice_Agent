import os
import time
import requests
import mimetypes

SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")

def transcribe_local_file(file_path: str, mode: str = "transcribe") -> str:
    """
    Reads a local audio file and sends it to Sarvam AI for transcription.
    
    Available modes for saaras:v3:
    - "transcribe" (Default: Native script)
    - "translate"  (Translates to English)
    - "codemix"    (English words in Latin, Indic words in native script)
    """
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY environment variable is not set.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file '{file_path}' not found.")

    # Automatically determine the correct MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "audio/wav"  # Default fallback

    headers = {
        "api-subscription-key": SARVAM_API_KEY
        # Do NOT set Content-Type; 'requests' calculates the multipart boundary automatically
    }

    # Prepare form data
    data = {
        "model": "saaras:v3",  # Sarvam's recommended multi-lingual model
        "mode": mode
    }

    print(f"Uploading '{file_path}' to Sarvam AI...")
    
    with open(file_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(file_path), audio_file, mime_type)
        }

        start = time.perf_counter()
        response = requests.post(
            SARVAM_API_URL, 
            headers=headers, 
            files=files, 
            data=data, 
            timeout=60
        )
        elapsed = time.perf_counter() - start

    if response.status_code != 200:
        print(f"API Error ({response.status_code}): {response.text}")
        print(f"API response time: {elapsed:.2f} seconds")
        return ""

    result = response.json()
    print(f"API response time: {elapsed:.2f} seconds")
    return result.get("transcript", result.get("text", ""))


if __name__ == "__main__":
    # Change this to the exact name of your audio file on your device
    local_audio_path = "Hindi_test.mp3" 

    try:
        # You can change the mode to "codemix" or "translate" if needed
        transcript = transcribe_local_file(local_audio_path, mode="transcribe")
        
        if transcript:
            print("\n--- Transcription Result ---")
            print(transcript)
        else:
            print("No transcription returned.")
            
    except Exception as e:
        print(f"An error occurred: {e}")