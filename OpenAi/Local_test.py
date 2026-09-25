import os
import time
from openai import OpenAI

def transcribe_local_file(file_path: str):
    # Initializes client and automatically loads OPENAI_API_KEY from the environment
    client = OpenAI()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file '{file_path}' not found.")

    print(f"Uploading '{file_path}' to OpenAI Whisper...")
    
    with open(file_path, "rb") as audio_file:
        # Whisper automatically detects the spoken language.
        # It will return Devanagari if you speak Hindi, or Gujarati script if you speak Gujarati.
        start = time.perf_counter()
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            # OPTIONAL: If you want to force it to expect a specific language and bypass 
            # auto-detection (which makes it slightly faster), uncomment the line below 
            # and use ISO-639-1 format (e.g., "hi" for Hindi, "gu" for Gujarati, "en" for English).
            # language="hi" 
        )
        elapsed = time.perf_counter() - start
        
    print("\n--- Transcription Result ---")
    print(transcription.text)
    print(f"API response time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    # Ensure this matches your actual audio file name
    transcribe_local_file("Hindi_test.mp3")