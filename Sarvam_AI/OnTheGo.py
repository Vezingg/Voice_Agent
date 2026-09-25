import os
import requests
import speech_recognition as sr
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

# Suppress low-level ALSA / JACK terminal noise
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
try:
    asound = cdll.LoadLibrary("libasound.so.2")
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass


SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")


def transcribe_audio_bytes(audio_bytes: bytes, language_code: str = "hi-IN") -> str:
    """Sends raw WAV bytes to Sarvam AI using multipart/form-data."""
    headers = {
        "api-subscription-key": SARVAM_API_KEY
        # Do NOT set Content-Type here; the requests library will automatically 
        # set it to multipart/form-data and calculate the boundaries.
    }
    
    # Sarvam requires the file to be uploaded as form data
    files = {
        "file": ("audio.wav", audio_bytes, "audio/wav")
    }
    
    # Define the language code (e.g., 'hi-IN' for Hindi, 'en-IN' for Indian English)
    data = {
        "language_code": language_code,
        "model": "saarika:v1" # Or omit if the API defaults to the latest
    }

    response = requests.post(
        SARVAM_API_URL, 
        headers=headers, 
        files=files, 
        data=data, 
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"\nAPI Error ({response.status_code}): {response.text}")
        return ""
        
    result = response.json()
    # Handle possible key variations in the response (usually 'transcript' or 'text')
    return result.get("transcript", result.get("text", ""))


def listen_and_transcribe(silence_duration: float = 2.0):
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY environment variable not set.")

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = silence_duration
    recognizer.dynamic_energy_threshold = True

    # device_index=0 targets the WSLg virtual PulseAudio device
    with sr.Microphone(device_index=0, sample_rate=16000) as source:
        print("Calibrating ambient room noise (stay quiet for 1s)...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"Microphone ready. Speak (pause for {silence_duration}s to send to Sarvam)...")
        print("Press Ctrl+C to terminate.\n")

        while True:
            try:
                print("Listening...")
                audio_data = recognizer.listen(source)

                print("Transcribing via Sarvam AI...")
                wav_bytes = audio_data.get_wav_data()
                
                # You can change language_code to 'en-IN', 'gu-IN', etc.
                transcript = transcribe_audio_bytes(wav_bytes, language_code="hi-IN")

                if transcript.strip():
                    print(f"Result: {transcript.strip()}\n")
                else:
                    print("No speech detected.\n")

            except KeyboardInterrupt:
                print("\nStopping audio listener.")
                break
            except Exception as e:
                print(f"Capture error: {e}\n")


if __name__ == "__main__":
    listen_and_transcribe(silence_duration=2.0)