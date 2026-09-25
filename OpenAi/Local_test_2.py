import os
from openai import OpenAI

def transcribe_local_file(file_path: str):
    client = OpenAI()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file '{file_path}' not found.")

    print(f"Uploading '{file_path}' to OpenAI Whisper...")
    
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            # 1. Omit the language parameter to avoid the 400 error
            
            # 2. OPTIONAL: Nudge the model into Gujarati using the prompt parameter
            prompt="આ ગુજરાતી છે." 
        )
        
    print("\n--- Transcription Result ---")
    print(transcription.text)

if __name__ == "__main__":
    transcribe_local_file("Gujarati_test.mp3")