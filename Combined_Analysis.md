# Combined Voice Model Analysis

Scoring scale: **10 = excellent**, **0 = unusable**.

- **Accuracy** means how closely the transcript matches the spoken words in the audio.
- **Correctness** means how usable the final text is, including the right language/script, completeness, punctuation, and avoiding hallucinated words.
- **Latency** is the API round-trip time from sending the audio until the transcript comes back, taken from `Analysis.md`.

## Audio Reference Summary

| Audio file | Spoken content summary |
|---|---|
| `harvard.wav` | English Harvard sentence sample: "The stale smell of old beer lingers..." |
| `Gujarati_test.mp3` | Gujarati paneer recipe narration, mainly about Punjabi dhaba style paneer sabzi and adding whole spices. |
| `Hindi_test.mp3` | Hindi paneer tikka masala recipe introduction, asking viewers to like, subscribe, and click the bell icon. |
| `Marathi_test.mp3` | Marathi paneer tikka masala recipe step, discussing marination, paneer, capsicum, tomato/onion alternatives, and available ingredients. |

## Overall Ranking

Quality ranking is unchanged. Latency is shown as an average across the four test files.

| Rank | Model | Overall accuracy | Overall correctness | Avg latency | Notes |
|---:|---|---:|---:|---:|---|
| 1 | `saaras:v3` | 9.6/10 | 9.6/10 | 1.91s | Best multilingual performance and fastest among the usable Indic models. |
| 2 | `Deepgram nova-3` | 9.0/10 | 9.1/10 | 3.19s | Very strong overall. Gujarati and Hindi are good; Marathi has a few word mistakes. |
| 3 | `google/chirp` | 9.0/10 | 8.5/10 | 10.81s | Strong native-script Indic output, but much slower than Sarvam and Deepgram. |
| 4 | `AssemblyAI` | 6.8/10 | 6.0/10 | 11.52s | Excellent English, decent phonetic Marathi, but Gujarati/Hindi are incomplete or wrong-script, and it is the slowest. |
| 5 | `OpenAI whisper-1` | 6.3/10 | 5.3/10 | 6.87s | English is perfect, but Indic output often uses the wrong script. Slow on 30s files. |
| 6 | `openai/whisper-large-v3-turbo` via Hugging Face | 5.4/10 | 5.3/10 | 3.24s | Fast on English/Gujarati, but Gujarati output failed and Marathi was hallucinated. |

## Per-File Model Ratings

### `harvard.wav` - English

All models transcribed the English sample correctly. Google Chirp missed capitalization and punctuation.

| Model | Accuracy | Correctness | Latency | Result |
|---|---:|---:|---:|---|
| `openai/whisper-large-v3-turbo` | 10/10 | 10/10 | 0.5s | Perfect. Fastest. |
| `saaras:v3` | 10/10 | 10/10 | 0.7s | Perfect. |
| `Deepgram nova-3` | 10/10 | 10/10 | 1.0s | Perfect. |
| `OpenAI whisper-1` | 10/10 | 10/10 | 1.3s | Perfect. |
| `google/chirp` | 9.5/10 | 8/10 | 8.0s | Words are correct, but output is lowercase with no punctuation. |
| `AssemblyAI` | 10/10 | 10/10 | 10.0s | Perfect, but slowest on English. |

### `Gujarati_test.mp3` - Gujarati

Reference expectation: Gujarati script transcript about making Punjabi dhaba style paneer sabzi.

| Model | Accuracy | Correctness | Latency | Result |
|---|---:|---:|---:|---|
| `saaras:v3` | 9.5/10 | 9.5/10 | 2.4s | Best Gujarati result. Native Gujarati script, complete, and very close to the speech. |
| `Deepgram nova-3` | 9/10 | 9/10 | 3.92s | Very good Gujarati output. Minor wording/spacing issues, but meaning and sequence are correct. |
| `google/chirp` | 9/10 | 9/10 | 11.74s | Strong native Gujarati script, close to Sarvam/Deepgram, but much slower. |
| `AssemblyAI` | 3/10 | 2/10 | 12.03s | Detected the language incorrectly as Nepali, used Devanagari, and returned only a partial transcript. |
| `OpenAI whisper-1` | 2/10 | 1/10 | 8.73s | Some Gujarati-sounding words are present, but the script is wrong/mixed and the output degrades into hallucinated text. |
| `openai/whisper-large-v3-turbo` | 1/10 | 1/10 | 1.2s | Fastest, but almost unusable. Very short, incomplete, and mixed-script output. |

### `Hindi_test.mp3` - Hindi

Reference expectation: Hindi/Devanagari transcript about restaurant-style paneer tikka masala.

| Model | Accuracy | Correctness | Latency | Result |
|---|---:|---:|---:|---|
| `saaras:v3` | 9.5/10 | 9.5/10 | 2.27s | Best Hindi result. Complete, natural Devanagari, and accurate punctuation. Fastest usable Hindi result. |
| `Deepgram nova-3` | 9/10 | 9/10 | 3.92s | Very good. Slight code-mixing with English words like `restaurant`, `taste`, and `subscribe`, but the meaning is correct. |
| `google/chirp` | 9/10 | 8.5/10 | 11.74s | Complete and accurate Devanagari, but no punctuation. Slow. |
| `openai/whisper-large-v3-turbo` | 8.5/10 | 8/10 | 5.63s | Mostly correct Devanagari transcript with some spelling and wording mistakes. |
| `OpenAI whisper-1` | 7/10 | 4/10 | 8.73s | Phonetically captures much of the speech, but outputs Urdu/Arabic script instead of expected Hindi Devanagari. |
| `AssemblyAI` | 5/10 | 5/10 | 12.03s | Correct language detection and good start, but the transcript is cut off early. Slowest. |

### `Marathi_test.mp3` - Marathi

Reference expectation: Marathi transcript in Devanagari about paneer tikka masala preparation.

| Model | Accuracy | Correctness | Latency | Result |
|---|---:|---:|---:|---|
| `saaras:v3` | 9/10 | 9/10 | 2.27s | Best Marathi result. Native Devanagari and mostly accurate. Fastest usable Marathi result. |
| `google/chirp` | 8.5/10 | 8.5/10 | 11.74s | Strong native Devanagari Marathi, close to Sarvam, but slow. |
| `Deepgram nova-3` | 8/10 | 8/10 | 3.92s | Good and usable. Some Marathi word errors, but it keeps the main content and sequence. |
| `AssemblyAI` | 8/10 | 5/10 | 12.03s | Phonetically good, but romanized output makes it less correct for Marathi transcription use. Slowest. |
| `OpenAI whisper-1` | 7/10 | 4/10 | 8.73s | Captures the rough Marathi speech phonetically, but uses romanized text and has multiple word errors. |
| `openai/whisper-large-v3-turbo` | 2/10 | 2/10 | 5.63s | Mostly hallucinated English/repeated phrases and does not match the Marathi audio. |

## Latency Snapshot

| Model | English | Gujarati | Hindi | Marathi | Average |
|---|---:|---:|---:|---:|---:|
| `saaras:v3` | 0.7s | 2.4s | 2.27s | 2.27s | 1.91s |
| `Deepgram nova-3` | 1.0s | 3.92s | 3.92s | 3.92s | 3.19s |
| `openai/whisper-large-v3-turbo` | 0.5s | 1.2s | 5.63s | 5.63s | 3.24s |
| `OpenAI whisper-1` | 1.3s | 8.73s | 8.73s | 8.73s | 6.87s |
| `google/chirp` | 8.0s | 11.74s | 11.74s | 11.74s | 10.81s |
| `AssemblyAI` | 10.0s | 12.03s | 12.03s | 12.03s | 11.52s |

## Final Recommendation

For this test set, **`saaras:v3` is the best overall model**. It has the strongest Gujarati, Hindi, and Marathi transcripts, and it is also the **fastest among the models that actually work for Indic audio** (about 2.3s on the 30-second files).

**Deepgram nova-3** is the second-best option. Quality is close, and latency is still reasonable (about 3.9s on the 30-second files), with a bit more Marathi word error and Hindi code-mixing.

**Google Chirp** is quality-competitive with Deepgram on Indic scripts, but latency is much worse (about 11.7s on the 30-second files).

For this project, if the priority is multilingual Indian-language transcription, use:

1. **`saaras:v3`** as the primary model (best quality + lowest usable latency).
2. **`Deepgram nova-3`** as the backup model.
3. Avoid relying on **Hugging Face Whisper large-v3-turbo** for Gujarati/Marathi in this setup, because it failed badly on those two files even though it is fast on English.
4. Avoid **AssemblyAI** and **OpenAI whisper-1** as the main Indic path: they are slower and often return the wrong script or incomplete text.

Here is the pricing breakdown for the models evaluated in the combined analysis:

| Model | Provider | Cost per Minute | Cost per Hour | Free Tier / Trial Context |
| --- | --- | --- | --- | --- |
| **`saaras:v3`**<br> | Sarvam AI | ~₹0.15–₹0.20 (~$0.002) | ~$0.11–$0.14 | Free starter credits provided upon dashboard sign-up. |
| **`Deepgram nova-3`**<br> | Deepgram | $0.0043 | $0.26 | $200 in free credits instantly upon account creation. |
| **`AssemblyAI`**<br> | AssemblyAI (Universal 3.5 Pro) | ~$0.0061 | $0.37 | $50 in free credits instantly upon account creation. |
| **`OpenAI whisper-1`**<br> | OpenAI | $0.006 | $0.36 | Standard API billing with no recurring free tier. |
| **`openai/whisper-large-v3-turbo`**<br> | Hugging Face (Serverless Router) | $0.00 | $0.00 | The shared inference router is free but strictly rate-limited for production use. |
| **`google/chirp`**<br> | Google Cloud Speech-to-Text | billed per Google Speech-to-Text Chirp usage | billed per Google Speech-to-Text Chirp usage | Google Cloud free-trial credits apply if the project still has them. |
