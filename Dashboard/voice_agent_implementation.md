# Voice agent API implementation

This file is the source of truth for how **this dashboard** talks to Sarvam. A new agent should copy these URLs, header names, and JSON/form field names exactly. Pricing and latency notes live in `../Sarvam.md`.

## Architecture

```
Browser (index.html)
  POST /transcribe   multipart audio
  POST /speak        JSON text
        │
        ▼
Flask (app.py, port 5000)
        │
        ├── POST https://api.sarvam.ai/speech-to-text     (Saaras v3)
        ├── POST https://api.sarvam.ai/translate          (Mayura v1, only if translate=true)
        └── POST https://api.sarvam.ai/text-to-speech     (Bulbul v3)
```

Base URL is `https://api.sarvam.ai` with **no `/v1` prefix**. That `/v1` path is only for Sarvam’s OpenAI-compatible chat API, not these three.

Auth for every Sarvam call:

```
api-subscription-key: <SARVAM_API_KEY>
```

Not `Authorization: Bearer`. The key comes from the environment variable `SARVAM_API_KEY`.

---

## 1. Voice to text (STT)

| Item | Value |
|---|---|
| Product name | Saaras v3 |
| Model keyword | `saaras:v3` |
| Method | `POST` |
| URL | `https://api.sarvam.ai/speech-to-text` |
| Content type | `multipart/form-data` (file upload, not JSON) |
| Language | Auto-detected. Do **not** send a language field. |

### Exact fields this project sends

Multipart form:

| Field | Type | Required | Value in this project |
|---|---|---|---|
| `file` | file | yes | Audio bytes. Browser sends `recording.webm` from the mic or an uploaded `audio/*` file. |
| `model` | text | yes | `saaras:v3` |
| `mode` | text | yes | `transcribe` |

Header: `api-subscription-key` only (no JSON Content-Type).

Python equivalent of `app.py`:

```python
files = {"file": (filename, file_bytes, content_type)}
data = {"model": "saaras:v3", "mode": "transcribe"}
headers = {"api-subscription-key": SARVAM_API_KEY}

response = requests.post(
    "https://api.sarvam.ai/speech-to-text",
    headers=headers,
    files=files,
    data=data,
    timeout=60,
)
transcript = response.json().get("transcript") or response.json().get("text") or ""
```

`mode` must be `transcribe`. Do not use speech-to-text-translate here. Translation is a separate API.

### cURL

```bash
curl -X POST https://api.sarvam.ai/speech-to-text \
  -H "api-subscription-key: $SARVAM_API_KEY" \
  -F "file=@clip.mp3" \
  -F "model=saaras:v3" \
  -F "mode=transcribe"
```

### Response this code reads

```json
{
  "transcript": "…"
}
```

Fallback key: `text` if `transcript` is missing.

### Local Flask wrapper the UI actually calls

Browser never talks to Sarvam directly.

```
POST /transcribe
Content-Type: multipart/form-data
file: <blob>
client_audio_seconds: <optional number, for latency logging>
```

Flask returns:

```json
{
  "transcript": "…",
  "timings": {
    "transcription_seconds": 2.367,
    "audio_duration_seconds": 30.0,
    "transcript_word_count": 69,
    "transcript_char_count": 403
  }
}
```

---

## 2. Text to text translation

| Item | Value |
|---|---|
| Product name | Mayura v1 |
| Model keyword | `mayura:v1` |
| Method | `POST` |
| URL | `https://api.sarvam.ai/translate` |
| Content type | `application/json` |
| When it runs | Only if the UI checkbox **Translate first** is on (`translate: true` on `/speak`) |

TTS does **not** translate. English text + `language_code: hi-IN` makes Bulbul *pronounce English with a Hindi voice*. To speak Hindi words, call Mayura first, then TTS on `translated_text`.

### Exact JSON this project sends

```json
{
  "input": "<chunk of source text>",
  "source_language_code": "auto",
  "target_language_code": "hi-IN",
  "model": "mayura:v1",
  "mode": "formal"
}
```

| Keyword | Required | This project |
|---|---|---|
| `input` | yes | Source string. Chunked to **900 characters** (`TRANSLATE_MAX_CHARS`) because Mayura v1 max is 1000. |
| `source_language_code` | yes | `auto` (Mayura v1 supports auto-detect) |
| `target_language_code` | yes | Same BCP-47 code as the TTS language dropdown: `hi-IN`, `mr-IN`, `en-IN`, … |
| `model` | yes here | `mayura:v1` (not `sarvam-translate:v1`) |
| `mode` | yes here | `formal` |

Allowed `target_language_code` values used by this app (same set as TTS):

`bn-IN`, `en-IN`, `gu-IN`, `hi-IN`, `kn-IN`, `ml-IN`, `mr-IN`, `od-IN`, `pa-IN`, `ta-IN`, `te-IN`

Headers:

```
api-subscription-key: <key>
Content-Type: application/json
```

Python equivalent of `translate_text()` in `app.py`:

```python
response = requests.post(
    "https://api.sarvam.ai/translate",
    headers={
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "input": chunk,
        "source_language_code": "auto",
        "target_language_code": target_language_code,
        "model": "mayura:v1",
        "mode": "formal",
    },
    timeout=60,
)
translated = response.json()["translated_text"]
```

### cURL

```bash
curl -X POST https://api.sarvam.ai/translate \
  -H "api-subscription-key: $SARVAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, how are you?",
    "source_language_code": "auto",
    "target_language_code": "hi-IN",
    "model": "mayura:v1",
    "mode": "formal"
  }'
```

### Response this code reads

```json
{
  "translated_text": "नमस्ते, आप कैसे हैं?",
  "source_language_code": "en-IN",
  "request_id": "…"
}
```

Only `translated_text` is used. Chunks are joined with a space.

There is **no** dedicated `/translate` Flask route. Translation happens inside `POST /speak` when `translate` is true.

---

## 3. Text to voice (TTS)

| Item | Value |
|---|---|
| Product name | Bulbul v3 |
| Model keyword | `bulbul:v3` |
| Method | `POST` |
| URL | `https://api.sarvam.ai/text-to-speech` |
| Content type | `application/json` |
| REST type | JSON REST (`convert`), not WebSocket / HTTP stream |

Chrome on Windows plays this output as MP3. Do not switch back to WAV without a Chrome playback check.

### Exact JSON this project sends

```json
{
  "text": "<chunk of text to speak>",
  "language_code": "hi-IN",
  "model": "bulbul:v3",
  "speaker": "shubh",
  "output_audio_codec": "mp3",
  "speech_sample_rate": 22050
}
```

| Keyword | Required | This project | Notes |
|---|---|---|---|
| `text` | yes | Spoken string (already translated if that flag was on) | Max **2500** chars on v3. This app chunks at **2400**. |
| `language_code` | yes | BCP-47 from the UI | Current REST name is `language_code`. Older SDKs used `target_language_code`. Do **not** send `target_language_code` on this REST call. |
| `model` | yes here | `bulbul:v3` | |
| `speaker` | no (default `shubh`) | lowercase UI value | Must be a v3 voice. v2 names like `anushka` fail. |
| `output_audio_codec` | no (default `wav`) | `mp3` | Chrome-safe. Allowed: `mp3`, `wav`, `aac`, `opus`, `flac`, `linear16`, `mulaw`, `alaw`. |
| `speech_sample_rate` | no | `22050` | Matches Sarvam playground “22k”. Also valid: 8000, 16000, 24000, 32000, 44100, 48000. |

Do **not** send `pitch` or `loudness` with `bulbul:v3` (API returns 400). `pace` is allowed (0.5–2.0) but this project leaves it at default `1.0`.

Default speaker: `shubh`. Full v3 list in `TTS_SPEAKERS` in `app.py` (all lowercase).

Python equivalent of `synthesize_chunk()`:

```python
response = requests.post(
    "https://api.sarvam.ai/text-to-speech",
    headers={
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "text": text,
        "language_code": language_code,
        "model": "bulbul:v3",
        "speaker": speaker,
        "output_audio_codec": "mp3",
        "speech_sample_rate": 22050,
    },
    timeout=90,
)
audio_bytes = b"".join(
    base64.b64decode(item) for item in response.json()["audios"]
)
```

### cURL

```bash
curl -X POST https://api.sarvam.ai/text-to-speech \
  -H "api-subscription-key: $SARVAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "नमस्ते, आप कैसे हैं?",
    "language_code": "hi-IN",
    "model": "bulbul:v3",
    "speaker": "shubh",
    "output_audio_codec": "mp3",
    "speech_sample_rate": 22050
  }'
```

### Response this code reads

```json
{
  "request_id": "…",
  "audios": ["<base64 mp3 string>", "…"]
}
```

Decode every entry in `audios` and concatenate bytes. For a single chunk that is one MP3. Multiple TTS chunks are concatenated with `b"".join(chunks)` (MP3 frame concat). WAV concat uses `concat_wavs()` only if codec is `wav`.

Browser playback MIME: `audio/mpeg`. The UI builds a `Blob` and `URL.createObjectURL`, not a `data:` WAV URL.

### Local Flask wrapper the UI actually calls

```
POST /speak
Content-Type: application/json
```

```json
{
  "text": "Hello, how are you?",
  "format": "text",
  "language_code": "hi-IN",
  "speaker": "shubh",
  "translate": true
}
```

| Field | Meaning |
|---|---|
| `text` | Typed text or contents of a `.txt` / `.md` file |
| `format` | `text` or `markdown` (markdown is stripped before APIs) |
| `language_code` | TTS language **and** Mayura `target_language_code` |
| `speaker` | Bulbul v3 voice, lowercase |
| `translate` | `true` → Mayura then Bulbul. `false` → Bulbul only |

Flask then:

1. If `translate`: Mayura `mayura:v1` with `target_language_code = language_code`
2. Chunk spoken text at 2400 chars
3. Call Bulbul per chunk (up to 3 parallel)
4. Return one MP3 as base64

```json
{
  "audio": "<base64 mp3>",
  "mime": "audio/mpeg",
  "spoken_text": "नमस्ते, आप कैसे हैं?",
  "translated": true,
  "timings": {
    "translate_seconds": 1.501,
    "tts_seconds": 2.274,
    "total_seconds": 3.775,
    "input_word_count": 27,
    "input_char_count": 127,
    "spoken_word_count": 31,
    "spoken_char_count": 141,
    "output_audio_duration_seconds": 7.595
  }
}
```

---

## End-to-end sequences

### A. Mic / file → transcript

1. UI `POST /transcribe` with audio file
2. Flask `POST https://api.sarvam.ai/speech-to-text`  
   `model=saaras:v3` `mode=transcribe`

### B. Type English, speak English (no checkbox)

1. UI `POST /speak` `{ translate: false, language_code: "en-IN", … }`
2. Flask `POST https://api.sarvam.ai/text-to-speech`  
   `model=bulbul:v3` `language_code=en-IN` `output_audio_codec=mp3`

### C. Type English, speak Hindi (checkbox on)

1. UI `POST /speak` `{ translate: true, language_code: "hi-IN", … }`
2. Flask `POST https://api.sarvam.ai/translate`  
   `model=mayura:v1` `source_language_code=auto` `target_language_code=hi-IN`
3. Flask `POST https://api.sarvam.ai/text-to-speech`  
   `text=<translated_text>` `language_code=hi-IN` `model=bulbul:v3` `output_audio_codec=mp3`

---

## Keywords cheat sheet

| Purpose | Keyword | Exact string |
|---|---|---|
| Auth header | header name | `api-subscription-key` |
| STT model | `model` | `saaras:v3` |
| STT mode | `mode` | `transcribe` |
| STT file field | form field | `file` |
| Translate model | `model` | `mayura:v1` |
| Translate source | `source_language_code` | `auto` |
| Translate target | `target_language_code` | e.g. `hi-IN` |
| Translate input | `input` | string |
| Translate style | `mode` | `formal` |
| TTS model | `model` | `bulbul:v3` |
| TTS text | `text` | string |
| TTS language | `language_code` | e.g. `hi-IN` |
| TTS voice | `speaker` | e.g. `shubh` |
| TTS codec | `output_audio_codec` | `mp3` |
| TTS sample rate | `speech_sample_rate` | `22050` (number, not `"22k"`) |
| TTS audio list | response | `audios` (base64 array) |
| STT text | response | `transcript` |
| Translate text | response | `translated_text` |

## Limits this code already handles

| API | Limit | This app |
|---|---|---|
| Mayura v1 | 1000 chars / request | chunks at 900 |
| Bulbul v3 REST | 2500 chars / request | chunks at 2400 |
| Saaras REST | ~30s audio in some plans | dashboard sends the whole file as-is (chunking STT lives in `Dashboard/chunking/`) |

## Files

| File | Role |
|---|---|
| `Dashboard/app.py` | Flask + all three Sarvam calls |
| `Dashboard/index.html` | UI; calls `/transcribe` and `/speak` only |
| `Dashboard/latency_log.json` | Append-only timing log |
| `../Sarvam.md` | Pricing + measured latency |

Official docs: [STT](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview), [Translate](https://docs.sarvam.ai/api-reference/text/translate-text), [TTS REST](https://docs.sarvam.ai/api-reference/text-to-speech/convert).
