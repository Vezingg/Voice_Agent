import os
import time
import assemblyai as aai

def transcribe_local_file(file_path: str):
    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the ASSEMBLYAI_API_KEY environment variable.")
    
    aai.settings.api_key = api_key

    # Use the new speech_models array syntax required by the latest SDK
    config = aai.TranscriptionConfig(
        language_detection=True,
        speech_models=["universal-3-5-pro", "universal-2"]
    )

    transcriber = aai.Transcriber()
    
    print(f"Uploading '{file_path}' to AssemblyAI...")
    start = time.perf_counter()
    transcript = transcriber.transcribe(file_path, config=config)
    elapsed = time.perf_counter() - start

    if transcript.status == aai.TranscriptStatus.error:
        print(f"\nAPI Error: {transcript.error}")
        print(f"API response time: {elapsed:.2f} seconds")
    else:
        print("\n--- Transcription Result ---")
        print(transcript.text)
        print(f"\n[Detected Language: {transcript.language_code}]")
        print(f"API response time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    transcribe_local_file("Hindi_test.mp3")