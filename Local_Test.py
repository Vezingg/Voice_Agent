import mimetypes
import os
import time
import requests

API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
HF_TOKEN = os.environ.get("HF_TOKEN")


def transcribe_audio(file_path: str, max_retries: int = 3) -> str:
  if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is not set.")

  # Automatically identify audio MIME type (audio/wav, audio/mpeg, etc.)
  mime_type, _ = mimetypes.guess_type(file_path)
  if not mime_type or not mime_type.startswith("audio/"):
    mime_type = "audio/wav"  # Default fallback

  headers = {
      "Authorization": f"Bearer {HF_TOKEN}",
      "Content-Type": mime_type,
  }

  with open(file_path, "rb") as f:
    audio_data = f.read()

  # Retry loop to automatically handle cold starts (HTTP 503)
  for attempt in range(max_retries):
    start = time.perf_counter()
    response = requests.post(
        API_URL, headers=headers, data=audio_data, timeout=90
    )
    elapsed = time.perf_counter() - start

    # 503 means the free serverless model is waking up from idle
    if response.status_code == 503:
      wait_time = response.json().get("estimated_time", 20)
      print(f"Model is waking up (cold start). Retrying in {int(wait_time)}s...")
      time.sleep(wait_time)
      continue

    if response.status_code != 200:
      print(f"API response time: {elapsed:.2f} seconds")
      raise RuntimeError(
          f"Inference failed ({response.status_code}): {response.text}"
      )

    result = response.json()
    transcript = result.get("text", "")
    print("\n--- Transcription ---")
    print(transcript)
    print(f"API response time: {elapsed:.2f} seconds")
    return transcript

  raise TimeoutError("Model took too long to load. Please try running again.")


if __name__ == "__main__":
  audio_path = "Hindi_test.mp3"

  if os.path.exists(audio_path):
    print("Transcribing...")
    transcribe_audio(audio_path)
  else:
    print(f"File '{audio_path}' not found.")