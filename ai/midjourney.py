import io
import requests
import gradio_client.exceptions

from abc import ABC
from gradio_client import Client
from registry import register_model, TextToImgModel, ModelInfo


@register_model(TextToImgModel)
class MidjourneyModel(TextToImgModel, ABC):
    def __init__(self):
        self.meta = ModelInfo(
            provider="MidJourney",
            version="Midjourney",
            description="Модель для генерации изображений по текстовому (только английский) описанию.",
            capabilities=[TextToImgModel],
            is_async=False
        )
        self.negative_prompt = (
            "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon,"
            "drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality,"
            "jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands,"
            "poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated,"
            "bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions,"
            "malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers,"
            "too many fingers, long neck")

    async def execute(self, prompt: str) -> io.BytesIO | None:
        try:
            client = Client(
                "mukaist/Midjourney",
                download_files=False
            )
            result = client.predict(
                prompt=prompt,
                negative_prompt=self.negative_prompt,
                use_negative_prompt=True,
                style="2560 x 1440",
                seed=0,
                width=1024,
                height=1024,
                guidance_scale=6,
                randomize_seed=True,
                api_name="/run"
            )
            result = result[0][0]
            if not result or not isinstance(result, dict):
                raise RuntimeError(f"Неожиданный результат от Gradio space: {result}")

            image_url = result['image']['url']
            return self._process_result(image_url)

        except gradio_client.exceptions.AppError as e:
            print(e)
            return None
        except requests.exceptions.RequestException as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def _process_result(image_url):
        try:
            response = requests.get(image_url, stream=True, timeout=60)
            response.raise_for_status()
            image_data = io.BytesIO(response.content)
            image_data.seek(0)
            return image_data
        except requests.exceptions.RequestException as e:
            print({e})
            raise
