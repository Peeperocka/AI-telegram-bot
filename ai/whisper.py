from gradio_client import Client, handle_file
from registry import AudioToTextModel, register_model, ModelInfo


@register_model(AudioToTextModel)
class WhisperModel:
    def __init__(self):
        self.meta = ModelInfo(
            provider="whisper",
            version="whisper-large-v3",
            description="Audio transcription model",
            capabilities=[AudioToTextModel],
            is_async=False,
            is_available_to_user=False
        )
        self.client = Client("hf-audio/whisper-large-v3")

    async def execute(self, audio_path: str) -> str:
        result = self.client.predict(
            inputs=handle_file(audio_path),
            task="transcribe",
            api_name="/predict_1"
        )
        return result
