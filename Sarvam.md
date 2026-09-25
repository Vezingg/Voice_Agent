# Sarvam models used in this project

This dashboard uses three Sarvam APIs. Official prices are in INR only ([Sarvam pricing](https://docs.sarvam.ai/api/pricing)). USD figures below use about **₹95.90 per $1** (25 Sep 2026).

## Models

### 1. Voice to text — Saaras v3

| | |
|---|---|
| **Name** | Saaras v3 |
| **API id** | `saaras:v3` |
| **Endpoint** | `POST https://api.sarvam.ai/speech-to-text` |
| **What it does** | Turns spoken audio into text. Language is auto-detected (no extra language-ID call). This project uses `mode: transcribe`. |
| **Official cost** | **₹30 per hour** of audio (~**$0.31 / hour**). Billed per second, rounded up. |
| **Per minute** | ₹0.50 (~$0.0052) |

### 2. Translation — Mayura v1

| | |
|---|---|
| **Name** | Mayura v1 |
| **API id** | `mayura:v1` |
| **Endpoint** | `POST https://api.sarvam.ai/translate` |
| **What it does** | Translates text between Indian languages and English (for example English → Hindi). Used only when **Translate first** is on, before TTS. |
| **Official cost** | **₹20 per 10,000 characters** (~**$0.21 / 10K chars**). Rounded to the nearest character. |
| **Per 1,000 characters** | ₹2 (~$0.021) |

### 3. Text to voice — Bulbul v3

| | |
|---|---|
| **Name** | Bulbul v3 |
| **API id** | `bulbul:v3` |
| **Endpoint** | `POST https://api.sarvam.ai/text-to-speech` |
| **What it does** | Reads text out loud in the selected language and speaker. It does **not** translate; it speaks the text it is given. |
| **Official cost** | **₹30 per 10,000 characters** (~**$0.31 / 10K chars**). Rounded to the nearest character. |
| **Per 1,000 characters** | ₹3 (~$0.031) |

## 1 hour of continuous use

STT is billed by **audio time**. Translate and TTS are billed by **characters**, so a 1-hour estimate needs a speech-rate assumption.

**Assumption:** about **150 words/minute** of continuous speech ≈ **50,000 characters per hour** of transcript (and a similar amount of Hindi after translation).

That is the full loop for 1 hour: listen → transcribe → translate → speak.

| Step | Model | 1-hour usage | INR | USD |
|---|---|---|---|---|
| Voice → text | Saaras v3 | 1 hour of audio | **₹30** | **~$0.31** |
| Translate | Mayura v1 | ~50,000 characters | **₹100** | **~$1.04** |
| Text → voice | Bulbul v3 | ~50,000 characters | **₹150** | **~$1.56** |
| **All three together** | | | **₹280** | **~$2.92** |

If speech is slower or faster, translate + TTS move with character count. STT stays **₹30 / $0.31** for a full hour of audio:

| Speech rate | Characters / hour | Full pipeline (INR) | Full pipeline (USD) |
|---|---|---|---|
| Slow (~120 wpm) | ~40,000 | ~₹230 | ~$2.40 |
| Typical (~150 wpm) | ~50,000 | **₹280** | **~$2.92** |
| Fast (~180 wpm) | ~62,000 | ~₹340 | ~$3.55 |

## Notes

- New Sarvam accounts get **₹100** (~$1.04) in free credits. Credits are shared across these APIs and do not expire.
- If **Translate first** is off, Mayura is not called, so 1 hour of STT + TTS is about **₹180 (~$1.88)** at the typical rate above.
- Sources: [docs.sarvam.ai/api/pricing](https://docs.sarvam.ai/api/pricing), [sarvam.ai/api-pricing](https://www.sarvam.ai/api-pricing).

## Latency analysis (25 Sep 2026)

Source: `Dashboard/latency_log.json`. Window: **07:18–09:13 UTC** (12:48–14:43 IST). **33** logged calls: **31 ok**, **2 errors** (TTS `concat_wavs is not defined` during a code change — excluded from timing stats).

| Task | Model | OK runs | Share of OK |
|---|---|---|---|
| Voice → text | Saaras v3 | 7 | 23% |
| Translate (when checked) | Mayura v1 | 5 | 16% of TTS jobs |
| Text → voice | Bulbul v3 | 24 | 77% |

All times below are **server-side API time** (not browser download/playback).

### Voice to text — Saaras v3

Every clip was a **30.0s** MP3. Marathi (`Marathi_test.mp3`, 69 words / 403 chars) was run 5 times; Hindi (`Hindi_test.mp3`, 108 words / 535 chars) was run 2 times.

| Metric | Min | Median | Mean | P90 | Max |
|---|---|---|---|---|---|
| Transcription time (s) | 1.75 | 2.37 | **2.41** | 3.01 | 3.10 |
| Realtime factor (API s / audio s) | 0.058 | 0.079 | **0.080** | 0.100 | 0.103 |
| Words in transcript | 69 | 69 | 80 | 108 | 108 |

| File | Runs | Mean STT (s) | Words | Chars | Mean s / audio s |
|---|---|---|---|---|---|
| Marathi_test.mp3 | 5 | **2.26** | 69 | 403 | 0.075 |
| Hindi_test.mp3 | 2 | **2.80** | 108 | 535 | 0.093 |

**Takeaway:** 30 seconds of speech transcribes in about **2.4 seconds** (~**12.5× faster than realtime**). Hindi was a bit slower than Marathi, but both clips are the same length, so the extra ~0.5s is more likely extra words (108 vs 69) plus normal API jitter than a language tax.

Individual STT runs: 1.75s, 2.00s, 2.17s, 2.37s, 2.51s, 3.01s, 3.10s.

### Translation — Mayura v1

Only runs with **Translate first** on (5 jobs). Mayura time is almost a **fixed ~1.5s**, even for very short text — that is request overhead, not per-character work.

| Metric | Min | Median | Mean | P90 | Max |
|---|---|---|---|---|---|
| Translate time (s) | 1.31 | 1.50 | **1.50** | 1.51 | 1.71 |
| Input characters | 15 | 127 | 138 | 127 | 403 |

| Target | Input | Direction (from preview) | Translate (s) | Share of that job’s total |
|---|---|---|---|---|
| mr-IN | 15 chars (“Hi how are you?”) | English → Marathi | 1.31 | 61% |
| hi-IN | 18 chars | English → Hindi | 1.51 | 58% |
| hi-IN | 127 chars | English → Hindi | 1.48 | 40% |
| hi-IN | 127 chars | English → Hindi | 1.50 | 40% |
| en-IN | 403 chars (Marathi clip) | Marathi → English | 1.71 | 21% |

**Takeaway:** Do not use “seconds per 100 characters” on short prompts — 15 chars in 1.31s looks like 8.7s/100 chars, which is overhead, not scale. On the 403-char Marathi→English job it was **0.42s / 100 chars**. For dashboard use, budget a flat **~1.3–1.7s** per translate call.

### Text to voice — Bulbul v3

24 successful TTS jobs (19 without translate, 5 after Mayura). Generation time tracks **how long the spoken audio is**, not a flat per-request cost.

| Group | Runs | Min TTS (s) | Median | Mean | Max |
|---|---|---|---|---|---|
| All TTS (voice step only) | 24 | 0.68 | 4.43 | **3.83** | 7.10 |
| TTS without translate | 19 | 0.68 | 4.55 | **4.17** | 7.10 |
| TTS after translate | 5 | 0.84 | 2.24 | **2.54** | 6.25 |

By prompt length (TTS step only, translate off):

| Prompt size | Example | Runs | Mean TTS (s) | Mean output audio (s) | Generate / output (RTF) |
|---|---|---|---|---|---|
| Short (~15–19 chars, 4 words) | “Hello how are you” | 3 | **0.75** | 1.22 | ~0.62 |
| Medium (127 chars, 27 words) | English paragraph | 1 | **2.16** | 6.74 | 0.32 |
| Long (403–535 chars) | 30s Marathi/Hindi transcript | 15 | **4.99** | 29.9 | **0.17** |

By language (translate off):

| Language | Runs | Typical prompt | Mean TTS (s) | Mean output audio (s) |
|---|---|---|---|---|
| Marathi `mr-IN` | 13 | 403 chars / 69 words | **5.03** | ~30 |
| Hindi `hi-IN` | 2 | 535 chars / 108 words | **4.68** | ~30 |
| English `en-IN` | 4 | mostly short greetings | **1.10** | mixed |

Long Marathi TTS range: **4.06–7.10s** (mean 5.03, median 4.76). One outlier at 7.10s; most sit between 4.1s and 5.2s.

**Takeaway:** For ~30 seconds of speech, Bulbul needs about **5 seconds** to generate (~**6× faster than realtime**). Short greetings feel slower *relative to output* (0.6 RTF) because the ~0.7s round trip is mostly fixed overhead.

### Combined pipeline

Typical **30s Marathi clip** (the main repeated test: STT then speak the transcript, no translate):

| Step | Mean (s) |
|---|---|
| Voice → text (Saaras v3) | **2.26** |
| Text → voice (Bulbul v3) | **5.03** |
| **Listen → transcribe → speak** | **7.29** |

Same clip **with translate**:

| Path | Mean (s) |
|---|---|
| STT only | 2.26 |
| STT + TTS (no Mayura) | **7.29** |
| Mayura + TTS on short English greeting | **2.15–2.60** |
| Mayura (Marathi→English, 403 chars) + TTS | **7.95** (1.71 translate + 6.25 TTS) |
| STT + Mayura + TTS on the 30s Marathi clip | **~10.2** |

Who dominates the clock:

- **Long audio / long text:** TTS is the slow step (~5s vs STT ~2.4s vs translate ~1.5s).
- **Short chat lines:** Translate can be **~60%** of total time (1.3s translate vs 0.8s TTS).
- **STT is the cheapest in time** of the three for 30s audio: it returns in ~8% of the clip length.

Speed vs size (what to plot later):

| Input | STT | Translate | TTS |
|---|---|---|---|
| 30s audio | ~2.4s | — | — |
| ~18 chars | — | ~1.5s | ~0.9s |
| ~127 chars | — | ~1.5s | ~2.2s |
| ~403–535 chars (~30s of speech) | — | ~1.7s | ~5.0s |

So **TTS scales with spoken length**, **translate is roughly constant in this set**, **STT scales with audio duration** (only 30s samples here, so that slope is not proven yet).

### Errors

Two TTS failures at 07:58:58 and 07:59:11 UTC: `name 'concat_wavs' is not defined`. Those were a local code bug during the MP3 switch, not a Sarvam outage. Both used the 403-char Marathi prompt.

### Practical budget

For this log, a realistic round-trip on a **30-second Indian-language clip**:

- Transcribe: **~2.4s**
- Optional translate: **~1.5s**
- Speak it back: **~5.0s**
- **Total: ~7.3s without translate, ~8.8–10s with translate**
