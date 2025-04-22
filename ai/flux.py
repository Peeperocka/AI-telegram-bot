import io
import requests
import gradio_client.exceptions
from gradio_client import Client
from registry import TextToImgModel, ModelInfo, register_model


@register_model(TextToImgModel)
class FluxModel(TextToImgModel):
    def __init__(self):
        self.meta = ModelInfo(
            provider="flux",
            version="FLUX.1-schnell",
            description="модель для генерации изображений по текстовому (только английский) описанию.",
            capabilities=[TextToImgModel],
            is_async=False
        )

    async def execute(self, prompt: str) -> io.BytesIO:
        try:
            client = Client(
                "black-forest-labs/FLUX.1-schnell",
                download_files=False
            )
            result = client.predict(
                prompt=prompt,
                seed=0,
                randomize_seed=True,
                width=1024,
                height=1024,
                num_inference_steps=4,
                api_name="/infer"
            )
            return self._process_result(result[0]['url'])
        except gradio_client.exceptions.AppError:
            return await self._use_backup(prompt)

    @staticmethod
    def _process_result(image_url):
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        return io.BytesIO(response.content)

    async def _use_backup(self, prompt):
        client = Client("lalashechka/FLUX_1", download_files=False)
        result = client.predict(prompt=prompt)
        return self._process_result(result['url'])
