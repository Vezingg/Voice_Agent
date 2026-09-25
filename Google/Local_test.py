import os
import time
from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

LOCATION = "us-central1"


def transcribe_local_file(file_path: str, project_id: str):
  # 1. Point the client to the regional endpoint instead of global
  client = SpeechClient(
      client_options=ClientOptions(
          api_endpoint=f"{LOCATION}-speech.googleapis.com"
      )
  )

  if not os.path.exists(file_path):
    raise FileNotFoundError(f"Audio file '{file_path}' not found.")

  with open(file_path, "rb") as f:
    audio_content = f.read()

  # 2. Configure Chirp 2 with auto language detection
  config = cloud_speech.RecognitionConfig(
      auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
      language_codes=["auto"],
      model="chirp_2",
  )

  # 3. Match the location in the recognizer path
  request = cloud_speech.RecognizeRequest(
      recognizer=f"projects/{project_id}/locations/{LOCATION}/recognizers/_",
      config=config,
      content=audio_content,
  )

  print(
      f"Uploading '{file_path}' to Google Cloud Chirp 2 ({LOCATION})..."
  )

  try:
    start = time.perf_counter()
    response = client.recognize(request=request)
    elapsed = time.perf_counter() - start

    print("\n--- Transcription Result ---")
    if not response.results:
      print("No transcription results returned.")
    for result in response.results:
      print(result.alternatives[0].transcript)
    print(f"API response time: {elapsed:.2f} seconds")

  except Exception as e:
    print(f"\nAPI Error: {e}")


if __name__ == "__main__":
  GCP_PROJECT_ID = "keycaco"
  transcribe_local_file("Hindi_test.mp3", GCP_PROJECT_ID)