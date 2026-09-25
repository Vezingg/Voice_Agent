import os
import io
import re
import json
import time
import wave
import base64
import threading
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATENCY_LOG_PATH = os.path.join(BASE_DIR, "latency_log.json")
LOG_LOCK = threading.Lock()

TTS_LANGUAGES = {
    "bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN",
    "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN",
}
TTS_SPEAKERS = {
    "shubh", "aditya", "ritu", "priya", "neha", "rahul", "pooja",
    "rohan", "simran", "kavya", "amit", "dev", "ishita", "shreya",
    "ratan", "varun", "manan", "sumit", "roopa", "kabir", "aayan",
    "ashutosh", "advait", "anand", "tanya", "tarun", "sunny", "mani",
    "gokul", "vijay", "shruti", "suhani", "mohit", "kavitha", "rehan",
    "soham", "rupali",
}

TTS_MAX_CHARS = 2400
TRANSLATE_MAX_CHARS = 900
TTS_CODEC = "mp3"
TTS_SAMPLE_RATE = 22050
TTS_MIME = "audio/mpeg"


def round_seconds(value):
    if value is None:
        return None
    return round(float(value), 3)


def count_words(text):
    return len(re.findall(r"\S+", text or ""))


def preview_text(text, limit=80):
    compact = re.sub(r"\s+", " ", (text or "")).strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "…"


def now_stamp():
    now = datetime.now().astimezone()
    return {
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
    }


def append_latency_log(entry):
    with LOG_LOCK:
        records = []
        if os.path.exists(LATENCY_LOG_PATH):
            try:
                with open(LATENCY_LOG_PATH, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                    if isinstance(loaded, list):
                        records = loaded
            except (json.JSONDecodeError, OSError):
                records = []
        records.append(entry)
        with open(LATENCY_LOG_PATH, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2, ensure_ascii=False)


def ratio(latency_seconds, amount):
    if not latency_seconds or not amount:
        return None
    return round_seconds(latency_seconds / amount)


def wav_duration_seconds(wav_bytes):
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            rate = wf.getframerate()
            if not rate:
                return None
            return round_seconds(wf.getnframes() / float(rate))
    except Exception:
        return None


def audio_duration_seconds(file_bytes, client_audio_seconds=None):
    duration = wav_duration_seconds(file_bytes)
    if duration:
        return duration
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(file_bytes))
        return round_seconds(len(audio) / 1000.0)
    except Exception:
        pass
    if client_audio_seconds not in (None, ""):
        try:
            return round_seconds(client_audio_seconds)
        except (TypeError, ValueError):
            return None
    return None


def sarvam_headers(json_body=False):
    headers = {"api-subscription-key": SARVAM_API_KEY}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def sarvam_error_message(response):
    try:
        data = response.json()
        err = data.get("error", data)
        if isinstance(err, dict):
            return err.get("message") or response.text
        if isinstance(err, str):
            return err
        return response.text
    except Exception:
        return response.text


def strip_markdown(text):
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]{1,3}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text, max_len):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    parts = re.split(r"(?<=[\.!?।।\n])\s+", text)
    chunks = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) > max_len:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(part), max_len):
                chunks.append(part[i:i + max_len])
            continue
        candidate = (current + " " + part).strip() if current else part
        if len(candidate) <= max_len:
            current = candidate
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def translate_text(text, target_language_code):
    pieces = []
    for chunk in chunk_text(text, TRANSLATE_MAX_CHARS):
        response = requests.post(
            SARVAM_TRANSLATE_URL,
            headers=sarvam_headers(json_body=True),
            json={
                "input": chunk,
                "source_language_code": "auto",
                "target_language_code": target_language_code,
                "model": "mayura:v1",
                "mode": "formal",
            },
            timeout=60,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Translate API Error ({response.status_code}): {sarvam_error_message(response)}"
            )
        translated = response.json().get("translated_text", "").strip()
        if translated:
            pieces.append(translated)
    if not pieces:
        raise RuntimeError("Translate API returned empty text.")
    return " ".join(pieces)


def synthesize_chunk(text, language_code, speaker):
    response = requests.post(
        SARVAM_TTS_URL,
        headers=sarvam_headers(json_body=True),
        json={
            "text": text,
            "language_code": language_code,
            "model": "bulbul:v3",
            "speaker": speaker,
            "output_audio_codec": TTS_CODEC,
            "speech_sample_rate": TTS_SAMPLE_RATE,
        },
        timeout=90,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"TTS API Error ({response.status_code}): {sarvam_error_message(response)}"
        )
    audios = response.json().get("audios") or []
    if not audios:
        raise RuntimeError("TTS API returned no audio.")
    return b"".join(base64.b64decode(item) for item in audios)


def concat_audio(chunks):
    if not chunks:
        raise RuntimeError("No audio generated.")
    if len(chunks) == 1:
        return chunks[0]
    if TTS_CODEC == "wav":
        return concat_wavs(chunks)
    return b"".join(chunks)


def concat_wavs(wav_chunks):
    if not wav_chunks:
        raise RuntimeError("No audio generated.")
    if len(wav_chunks) == 1:
        return wav_chunks[0]

    params = None
    frames = []
    for data in wav_chunks:
        with wave.open(io.BytesIO(data), "rb") as wf:
            if params is None:
                params = wf.getparams()
            elif wf.getparams()[:3] != params[:3]:
                raise RuntimeError("Cannot merge TTS chunks with different audio formats.")
            frames.append(wf.readframes(wf.getnframes()))

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setparams(params)
        for frame in frames:
            wf.writeframes(frame)
    return out.getvalue()


def output_audio_duration_seconds(data):
    duration = wav_duration_seconds(data)
    if duration:
        return duration
    try:
        from pydub import AudioSegment
        return round_seconds(len(AudioSegment.from_file(io.BytesIO(data))) / 1000.0)
    except Exception:
        if data:
            return round_seconds(len(data) * 8 / 128000.0)
        return None


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not SARVAM_API_KEY:
        return jsonify({"error": "SARVAM_API_KEY environment variable is not set."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_bytes = file.read()
    filename = file.filename
    content_type = file.content_type or "application/octet-stream"
    audio_seconds = audio_duration_seconds(
        file_bytes,
        request.form.get("client_audio_seconds"),
    )

    files = {
        "file": (filename, file_bytes, content_type)
    }
    data = {
        "model": "saaras:v3",
        "mode": "transcribe"
    }

    started = time.perf_counter()
    try:
        response = requests.post(
            SARVAM_STT_URL,
            headers=sarvam_headers(),
            files=files,
            data=data,
            timeout=60
        )
        transcription_seconds = round_seconds(time.perf_counter() - started)

        if response.status_code != 200:
            append_latency_log({
                **now_stamp(),
                "task": "voice_to_text",
                "model": "saaras:v3",
                "status": "error",
                "source_filename": filename,
                "audio_duration_seconds": audio_seconds,
                "transcription_seconds": transcription_seconds,
                "error": f"API Error ({response.status_code}): {response.text}",
            })
            return jsonify({
                "error": f"API Error ({response.status_code}): {response.text}",
                "timings": {
                    "transcription_seconds": transcription_seconds,
                    "audio_duration_seconds": audio_seconds,
                },
            }), 500

        result = response.json()
        transcript = result.get("transcript", result.get("text", "")) or ""
        word_count = count_words(transcript)
        char_count = len(transcript)
        log_entry = {
            **now_stamp(),
            "task": "voice_to_text",
            "model": "saaras:v3",
            "status": "ok",
            "source_filename": filename,
            "audio_duration_seconds": audio_seconds,
            "transcription_seconds": transcription_seconds,
            "transcript_word_count": word_count,
            "transcript_char_count": char_count,
            "seconds_per_audio_second": ratio(transcription_seconds, audio_seconds),
            "seconds_per_word": ratio(transcription_seconds, word_count),
            "text_preview": preview_text(transcript),
        }
        append_latency_log(log_entry)
        return jsonify({
            "transcript": transcript,
            "timings": {
                "transcription_seconds": transcription_seconds,
                "audio_duration_seconds": audio_seconds,
                "transcript_word_count": word_count,
                "transcript_char_count": char_count,
            },
        })

    except Exception as e:
        transcription_seconds = round_seconds(time.perf_counter() - started)
        append_latency_log({
            **now_stamp(),
            "task": "voice_to_text",
            "model": "saaras:v3",
            "status": "error",
            "source_filename": filename,
            "audio_duration_seconds": audio_seconds,
            "transcription_seconds": transcription_seconds,
            "error": str(e),
        })
        return jsonify({
            "error": str(e),
            "timings": {
                "transcription_seconds": transcription_seconds,
                "audio_duration_seconds": audio_seconds,
            },
        }), 500


@app.route("/speak", methods=["POST"])
def speak():
    if not SARVAM_API_KEY:
        return jsonify({"error": "SARVAM_API_KEY environment variable is not set."}), 500

    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    language_code = payload.get("language_code") or "hi-IN"
    speaker = (payload.get("speaker") or "shubh").strip().lower()
    translate = bool(payload.get("translate"))
    fmt = (payload.get("format") or "text").lower()

    if language_code not in TTS_LANGUAGES:
        return jsonify({"error": f"Unsupported language_code: {language_code}"}), 400
    if speaker not in TTS_SPEAKERS:
        return jsonify({"error": f"Unsupported speaker: {speaker}"}), 400
    if not text:
        return jsonify({"error": "No text to speak."}), 400

    if fmt == "markdown":
        text = strip_markdown(text)

    translate_seconds = None
    try:
        if translate:
            translate_started = time.perf_counter()
            spoken_text = translate_text(text, language_code)
            translate_seconds = round_seconds(time.perf_counter() - translate_started)
        else:
            spoken_text = text
            translate_seconds = None

        chunks = chunk_text(spoken_text, TTS_MAX_CHARS)
        if not chunks:
            return jsonify({"error": "No speakable text after processing."}), 400

        tts_started = time.perf_counter()
        wav_chunks = [None] * len(chunks)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(synthesize_chunk, chunk, language_code, speaker): i
                for i, chunk in enumerate(chunks)
            }
            for future in as_completed(futures):
                wav_chunks[futures[future]] = future.result()
        audio_bytes = concat_audio(wav_chunks)
        tts_seconds = round_seconds(time.perf_counter() - tts_started)
        total_seconds = round_seconds((translate_seconds or 0) + tts_seconds)

        input_word_count = count_words(text)
        input_char_count = len(text)
        spoken_word_count = count_words(spoken_text)
        spoken_char_count = len(spoken_text)
        output_audio_seconds = output_audio_duration_seconds(audio_bytes)

        timings = {
            "translate_seconds": translate_seconds,
            "tts_seconds": tts_seconds,
            "total_seconds": total_seconds,
            "input_word_count": input_word_count,
            "input_char_count": input_char_count,
            "spoken_word_count": spoken_word_count,
            "spoken_char_count": spoken_char_count,
            "output_audio_duration_seconds": output_audio_seconds,
        }
        append_latency_log({
            **now_stamp(),
            "task": "text_to_voice",
            "status": "ok",
            "translate": translate,
            "language_code": language_code,
            "speaker": speaker,
            "format": fmt,
            "models": {
                "translate": "mayura:v1" if translate else None,
                "tts": "bulbul:v3",
            },
            "input_word_count": input_word_count,
            "input_char_count": input_char_count,
            "spoken_word_count": spoken_word_count,
            "spoken_char_count": spoken_char_count,
            "tts_chunk_count": len(chunks),
            "translate_seconds": translate_seconds,
            "tts_seconds": tts_seconds,
            "total_seconds": total_seconds,
            "output_audio_duration_seconds": output_audio_seconds,
            "translate_seconds_per_100_chars": ratio(translate_seconds, (input_char_count / 100) if input_char_count else None),
            "tts_seconds_per_100_chars": ratio(tts_seconds, (spoken_char_count / 100) if spoken_char_count else None),
            "tts_seconds_per_word": ratio(tts_seconds, spoken_word_count),
            "text_preview": preview_text(text),
            "spoken_preview": preview_text(spoken_text),
        })
        return jsonify({
            "audio": base64.b64encode(audio_bytes).decode("ascii"),
            "mime": TTS_MIME,
            "spoken_text": spoken_text,
            "translated": translate,
            "timings": timings,
        })
    except Exception as e:
        append_latency_log({
            **now_stamp(),
            "task": "text_to_voice",
            "status": "error",
            "translate": translate,
            "language_code": language_code,
            "speaker": speaker,
            "format": fmt,
            "input_word_count": count_words(text),
            "input_char_count": len(text),
            "translate_seconds": translate_seconds,
            "error": str(e),
        })
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if not SARVAM_API_KEY:
        print("WARNING: SARVAM_API_KEY is not set.")
    app.run(debug=True, port=5000)
