from ctypes import CFUNCTYPE, c_char_p, c_int, c_void_p, cdll
import os
import requests
import speech_recognition as sr

# Suppress noisy C-level ALSA warnings in the terminal
ERROR_HANDLER_FUNC = CFUNCTYPE(
    None, c_char_p, c_int, c_char_p, c_int, c_char_p
)


def py_error_handler(filename, line, function, err, fmt):
  pass


c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
try:
  asound = cdll.LoadLibrary("libasound.so.2")
  asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
  pass

API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
HF_TOKEN = os.environ.get("HF_TOKEN")


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
  headers = {
      "Authorization": f"Bearer {HF_TOKEN}",
      "Content-Type": "audio/wav",
  }
  response = requests.post(
      API_URL, headers=headers, data=audio_bytes, timeout=60
  )
  if response.status_code != 200:
    print(f"\nInference error ({response.status_code}): {response.text}")
    return ""
  return response.json().get("text", "")


def listen_and_transcribe():
  if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable not set.")

  recognizer = sr.Recognizer()
  recognizer.pause_threshold = 2.0
  recognizer.dynamic_energy_threshold = True

  # Use device_index=0 to lock directly to 'pulse'
  with sr.Microphone(device_index=0, sample_rate=16000) as source:
    print("Calibrating background noise (stay quiet for 1s)...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Microphone ready. Start speaking (pause 1s to send)...")
    print("Press Ctrl+C to stop.\n")

    while True:
      try:
        print("Listening...")
        audio_data = recognizer.listen(source)

        print("Sending audio to Whisper...")
        wav_bytes = audio_data.get_wav_data()
        transcript = transcribe_audio_bytes(wav_bytes)

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
  listen_and_transcribe()