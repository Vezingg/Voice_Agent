# Live Speech-to-Text Pipeline (Whisper-Large-v3-Turbo)

## Purpose

This project’s audio-to-text path is defined **only** by `second_test.py`. Use that file’s model, API, and flow as the source of truth for any follow-on agent work (voice agents, streaming STT, etc.). Do not invent a different ASR stack unless explicitly asked.

## Dependencies (`requirements.txt`)

```
SpeechRecognition>=3.14.0
PyAudio>=0.2.14
requests>=2.31.0
```

| Package | Role |
|---|---|
| `SpeechRecognition` | Mic capture, ambient noise calibration, utterance segmentation (`listen`) |
| `PyAudio` | Backend for `speech_recognition.Microphone` |
| `requests` | HTTP POST of WAV bytes to Hugging Face Inference |

System needs: a working mic (PulseAudio/`pulse` on this machine), and ALSA/Pulse libs as required by PyAudio. Optional: `libasound.so.2` for the ALSA warning suppressor in the script.

## Auth / env

- Token: `HF_TOKEN` environment variable (Bearer token for Hugging Face).
- If unset, `listen_and_transcribe()` raises: `HF_TOKEN environment variable not set.`
- Do not hardcode tokens in code.

## Exact model and endpoint

- **Model:** `openai/whisper-large-v3-turbo`
- **API URL:** `https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo`
- **Method:** `POST` raw WAV body
- **Headers:**
  - `Authorization: Bearer <HF_TOKEN>`
  - `Content-Type: audio/wav`
- **Timeout:** 60 seconds
- **Success response:** JSON with a `"text"` field; empty / missing → treat as no speech
- **Non-200:** log status + body, return `""`

## Architecture / flow (`second_test.py`)

```
Mic (device_index=0, 16 kHz)
  → SpeechRecognition calibrates ambient noise (1s)
  → Loop: listen until pause (pause_threshold=2.0, dynamic energy)
  → audio_data.get_wav_data()  → WAV bytes
  → POST to HF Whisper large-v3-turbo
  → print transcript (or "No speech detected")
```

### 1. ALSA noise suppression (startup)

CTypes loads `libasound.so.2` and installs a no-op error handler so ALSA spam does not clutter the terminal. Failures are ignored.

### 2. `transcribe_audio_bytes(audio_bytes: bytes) -> str`

Single-shot inference helper:

1. Build auth + `audio/wav` headers.
2. `requests.post(API_URL, headers=..., data=audio_bytes, timeout=60)`.
3. On 200: `response.json().get("text", "")`.
4. On error: print and return `""`.

### 3. `listen_and_transcribe()` — live capture loop

1. Require `HF_TOKEN`.
2. `sr.Recognizer()` with:
   - `pause_threshold = 2.0` (end utterance after ~2s silence)
   - `dynamic_energy_threshold = True`
3. Open mic: `sr.Microphone(device_index=0, sample_rate=16000)`  
   - `device_index=0` is locked to Pulse (`pulse`) on this setup.
4. `adjust_for_ambient_noise(source, duration=1)`.
5. Infinite loop:
   - `recognizer.listen(source)` → utterance `AudioData`
   - `get_wav_data()` → WAV bytes
   - `transcribe_audio_bytes(wav_bytes)`
   - Print stripped transcript if non-empty; else “No speech detected.”
6. Exit cleanly on `KeyboardInterrupt`; other capture errors are printed and the loop continues.

### 4. Entry point

`python second_test.py` → `listen_and_transcribe()`.

## Contract for the next agent

When extending or rebuilding STT:

1. Keep **the same model**: `openai/whisper-large-v3-turbo` via the HF router URL above.
2. Keep **the same flow**: mic → SpeechRecognition listen → WAV bytes → HF Inference POST → `text`.
3. Keep **deps** aligned with `requirements.txt` unless you intentionally replace the stack.
4. Treat `second_test.py` as the reference implementation; mirror its helpers (`transcribe_audio_bytes`, mic settings) rather than re-deriving them from scratch.
