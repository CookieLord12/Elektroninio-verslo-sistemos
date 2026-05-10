import os
import uuid
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import dialogflowcx_v3 as dialogflowcx


# =========================
# CONFIG
# =========================

PROJECT_ID = 
LOCATION = 
AGENT_ID = 

DIALOGFLOW_LANGUAGE_CODE = "lt"
SPEECH_LANGUAGE_CODE = "lt-LT"
TTS_LANGUAGE_CODE = "lt-LT"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"voice-bot-service.json"

SAMPLE_RATE = 16000
CHANNELS = 1

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# AUDIO RECORDING
# =========================

def record_microphone_to_wav(output_path: str, seconds: int = 5) -> str:
    """
    Records microphone audio and saves it as 16 kHz mono WAV.
    """
    print(f"Recording for {seconds} seconds... Speak now.")

    recording = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()

    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(recording.tobytes())

    print(f"Saved recording: {output_path}")
    return output_path


# =========================
# SPEECH TO TEXT
# =========================

def transcribe_audio_file(audio_path: str) -> str:
    """
    Converts Lithuanian speech audio into text using Google Speech-to-Text.
    Audio should be WAV LINEAR16, mono, 16 kHz.
    """
    client = speech.SpeechClient()

    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code=SPEECH_LANGUAGE_CODE,
        enable_automatic_punctuation=True,
        model="command_and_search",
    )

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return ""

    transcript_parts = []

    for result in response.results:
        if result.alternatives:
            transcript_parts.append(result.alternatives[0].transcript)

    return " ".join(transcript_parts).strip()


# =========================
# DIALOGFLOW CX
# =========================

def ask_dialogflow(user_text: str, session_id: str) -> str:
    """
    Sends text to Dialogflow CX and returns the bot's text answer.
    """
    if not user_text.strip():
        return "Atsiprašau, nepavyko atpažinti jūsų klausimo."

    client_options = {
        "api_endpoint": f"{LOCATION}-dialogflow.googleapis.com:443"
    }

    client = dialogflowcx.SessionsClient(client_options=client_options)

    session_path = client.session_path(
        project=PROJECT_ID,
        location=LOCATION,
        agent=AGENT_ID,
        session=session_id,
    )

    text_input = dialogflowcx.TextInput(text=user_text)

    query_input = dialogflowcx.QueryInput(
        text=text_input,
        language_code=DIALOGFLOW_LANGUAGE_CODE,
    )

    request = dialogflowcx.DetectIntentRequest(
        session=session_path,
        query_input=query_input,
    )

    response = client.detect_intent(request=request)

    messages = response.query_result.response_messages

    answers = []

    for message in messages:
        if message.text and message.text.text:
            answers.extend(message.text.text)

    if answers:
        return " ".join(answers).strip()

    return "Atsiprašau, neradau tinkamo atsakymo."


# =========================
# TEXT TO SPEECH
# =========================

def synthesize_to_wav(text: str, output_path: str) -> str:
    """
    Converts Lithuanian text to speech and saves it as WAV.
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=TTS_LANGUAGE_CODE,
        name="lt-LT-Standard-B",
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_path, "wb") as output_file:
        output_file.write(response.audio_content)

    return output_path


def play_wav(audio_path: str) -> None:
    """
    Plays a WAV file through speakers.
    """
    try:
        with wave.open(audio_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())

        audio_data = np.frombuffer(frames, dtype=np.int16)

        if channels > 1:
            audio_data = audio_data.reshape(-1, channels)

        sd.play(audio_data, samplerate=sample_rate)
        sd.wait()

    except Exception as error:
        print(f"Could not play audio automatically: {error}")
        print(f"Audio saved here: {audio_path}")


# =========================
# ONE AUDIO FILE TEST
# =========================

def run_once_from_audio_file(audio_path: str) -> None:
    """
    Full pipeline:
    audio file → Speech-to-Text → Dialogflow CX → Text-to-Speech
    """
    session_id = str(uuid.uuid4())

    print("Transcribing audio...")
    user_text = transcribe_audio_file(audio_path)

    print(f"You said: {user_text}")

    bot_text = ask_dialogflow(user_text, session_id)

    print(f"Bot: {bot_text}")

    output_audio = str(OUTPUT_DIR / "bot_response.wav")
    synthesize_to_wav(bot_text, output_audio)
    play_wav(output_audio)


# =========================
# LIVE TEXT CHAT FUNCTION
# =========================

def live_text_chat() -> None:
    """
    Live terminal chat with Dialogflow.
    You type Lithuanian text, bot answers with text + voice.
    """
    session_id = str(uuid.uuid4())

    print("\nLive text chat started.")
    print("Type 'exit' to stop.\n")

    while True:
        user_text = input("You: ").strip()

        if user_text.lower() in {"exit", "quit", "stop", "baigti"}:
            print("Chat ended.")
            break

        bot_text = ask_dialogflow(user_text, session_id)

        print(f"Bot: {bot_text}")

        output_audio = str(OUTPUT_DIR / "bot_response.wav")
        synthesize_to_wav(bot_text, output_audio)
        play_wav(output_audio)


# =========================
# LIVE VOICE CHAT FUNCTION
# =========================

def live_voice_chat(record_seconds: int = 5) -> None:
    """
    Live voice chat:
    microphone → Speech-to-Text → Dialogflow CX → Text-to-Speech → speakers

    It records fixed-length voice turns.
    Press Enter to record each message.
    Type q to quit.
    """
    session_id = str(uuid.uuid4())

    print("\nLive voice chat started.")
    print("Press Enter to record.")
    print("Type 'q' and press Enter to stop.\n")

    while True:
        command = input("Press Enter to speak, or type q to quit: ").strip().lower()

        if command in {"q", "quit", "exit", "stop"}:
            print("Voice chat ended.")
            break

        user_audio = str(OUTPUT_DIR / "user_input.wav")

        record_microphone_to_wav(user_audio, seconds=record_seconds)

        print("Transcribing...")
        user_text = transcribe_audio_file(user_audio)

        if not user_text:
            print("Could not understand audio.")
            bot_text = "Atsiprašau, nepavyko atpažinti jūsų klausimo."
        else:
            print(f"You said: {user_text}")

            if user_text.lower() in {"baigti", "stop", "viso gero"}:
                print("Voice chat ended.")
                break

            bot_text = ask_dialogflow(user_text, session_id)

        print(f"Bot: {bot_text}")

        bot_audio = str(OUTPUT_DIR / "bot_response.wav")
        synthesize_to_wav(bot_text, bot_audio)
        play_wav(bot_audio)


# =========================
# MAIN MENU
# =========================

def main() -> None:
    print("Lithuanian Google Cloud Voice Chatbot")
    print("------------------------------------")
    print("1 - Live text chat")
    print("2 - Live voice chat")
    print("3 - Test one WAV audio file")
    print("0 - Exit")

    choice = input("\nChoose option: ").strip()

    if choice == "1":
        live_text_chat()

    elif choice == "2":
        seconds = input("Recording length in seconds, default 5: ").strip()

        if seconds.isdigit():
            live_voice_chat(record_seconds=int(seconds))
        else:
            live_voice_chat(record_seconds=5)

    elif choice == "3":
        audio_path = input("Enter WAV file path: ").strip()
        run_once_from_audio_file(audio_path)

    elif choice == "0":
        print("Exited.")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()