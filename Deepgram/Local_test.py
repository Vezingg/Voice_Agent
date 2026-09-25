import os
import time
from deepgram import DeepgramClient

def transcribe_local_file(file_path: str):
    # Initialize the client with empty parentheses. 
    # It automatically detects the DEEPGRAM_API_KEY environment variable.
    client = DeepgramClient()

    with open(file_path, "rb") as file:
        audio_data = file.read()

    print(f"Uploading '{file_path}' to Deepgram...")

    # Send the raw bytes using the latest v7 SDK syntax
    start = time.perf_counter()
    response = client.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-3",
        language="mr",
        smart_format=True,
    )
    elapsed = time.perf_counter() - start

    # Extract the transcript from the Pydantic response object
    transcript = response.results.channels[0].alternatives[0].transcript

    print("\n--- Transcription Result ---")
    print(transcript)
    print(f"API response time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    # Ensure this matches the audio file in your directory
    transcribe_local_file("Hindi_test.mp3")