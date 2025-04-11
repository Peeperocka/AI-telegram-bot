from gradio_client import Client, handle_file


def transcribe_audio(audio_path: str) -> str:
    client = Client("hf-audio/whisper-large-v3")
    try:
        result = client.predict(
            inputs=handle_file(audio_path),
            task="transcribe",
            api_name="/predict_1"
        )
        return result
    except Exception as e:
        print(f"Error during Whisper transcription: {e}")
        return f"Ошибка во время транскрипции, пожалуйста, попробуйте еще раз чуть позже"


if __name__ == '__main__':
    transcribe_audio("C:/Users/User/Music/audio_2025-04-11_03-46-30.ogg")
