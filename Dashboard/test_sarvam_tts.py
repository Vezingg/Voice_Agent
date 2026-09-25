from sarvamai import SarvamAI

client = SarvamAI(
    api_subscription_key="sk_4t6afq90_1KvrNd0PVoLOg0loTcEKxBHm",
)

response_stream = client.text_to_speech.convert_stream(
    text="""नमस्ते! Sarvam AI में आपका स्वागत है।

हम भारतीय भाषाओं के लिए अत्याधुनिक voice technology बनाते हैं। हमारे text-to-speech models प्राकृतिक और इंसान जैसी आवाज़ें produce करते हैं, जो बेहद realistic लगती हैं।

आप अपना text type कर सकते हैं या different voices को try करने के लिए किसी भी voice card पर play button पर click कर सकते हैं। तो चलिए, अपनी भाषा में AI की ताकत experience करें!""",
    language_code="hi-IN",
    speaker="shubh",
    model="bulbul:v3",
    pace=1,
    speech_sample_rate=22050,
    output_audio_codec="wav",
)

with open("speech.wav", "wb") as f:
    for chunk in response_stream:
        f.write(chunk)