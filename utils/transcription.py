import os
import tempfile
from io import BytesIO
from aiogram import types
from registry import AIRegistry, AudioToTextModel


async def transcribe_voice_message(message: types.Message, registry: AIRegistry) -> str | None:
    voice = message.voice
    if not voice:
        print("Error in transcribe_voice_message: message has no voice object.")
        return None

    try:
        whisper_model = registry.get_model("whisper", "whisper-large-v3")
        if not whisper_model:
            print("Transcription error: Whisper model 'whisper:whisper-large-v3' not found in registry.")
            return None

        if AudioToTextModel not in whisper_model.meta.capabilities:
            print(f"Transcription error: Model {whisper_model.meta.version} does not support AudioToText.")
            return None

        voice_bytes_io = BytesIO()
        await message.bot.download(voice, destination=voice_bytes_io)
        voice_bytes_io.seek(0)
        temp_audio_path = None
        transcription = None

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio_file:
            temp_audio_file.write(voice_bytes_io.read())
            temp_audio_path = temp_audio_file.name

        try:
            transcription_result = await whisper_model.execute(temp_audio_path)

            if isinstance(transcription_result, str):
                transcription = transcription_result.strip()
            else:
                print(f"Transcription error: Expected string response from Whisper, got {type(transcription_result)}")
                transcription = None

        except Exception as e:
            print(f"Transcription model execution failed: {e}")
            transcription = None

        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except OSError as e:
                    print(f"Error removing temporary audio file {temp_audio_path}: {e}")

        return transcription

    except Exception as e:
        print(f"Unexpected error in transcribe_voice_message process: {e}")
        return None
