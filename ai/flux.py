import io
from io import BytesIO

import requests
import gradio_client.exceptions

from gradio_client import Client
from typing import Union, Dict, Any

from registry import TextToImgModel, ModelInfo, register_model


class FluxGradioBaseModel(TextToImgModel):
    provider = "FLUX"

    def __init__(self,
                 gradio_space_id: str,
                 model_version: str,
                 description: str,
                 default_predict_params: Dict[str, Any],
                 capabilities: tuple = (TextToImgModel,)):
        self.gradio_space_id = gradio_space_id
        self.default_predict_params = default_predict_params

        self.meta = ModelInfo(
            provider=self.provider,
            version=model_version,
            description=description + " (Запросы только на английском).",
            capabilities=capabilities,
            is_async=False
        )

    async def execute(self, prompt: str) -> BytesIO | None:
        print(f"Executing model: {self.meta.version} via Gradio space: {self.gradio_space_id}")
        try:
            client = Client(
                self.gradio_space_id,
                download_files=False
            )

            predict_args = self.default_predict_params.copy()
            predict_args['prompt'] = prompt

            if 'api_name' not in predict_args:
                raise ValueError(f"Missing 'api_name' in default_predict_params for {self.gradio_space_id}")

            print(f"Calling predict with args: {predict_args}")
            result = client.predict(**predict_args)
            print(f"Received result from Gradio: {result}")
            result = result[0]

            image_url = self._parse_gradio_result(result)
            if not image_url:
                raise ValueError(f"Could not extract image URL/path from Gradio result: {result}")

            return self._process_result(image_url)

        except gradio_client.exceptions.AppError as e:
            print(f"Gradio AppError for {self.gradio_space_id}: {e}. Trying backup...")
            try:
                return await self._use_backup(prompt)
            except NotImplementedError:
                print(f"Backup is not implemented for {self.meta.version}")
                return None
            except Exception as backup_e:
                print(f"Backup mechanism failed for {self.meta.version}: {backup_e}")
                return None
        except (requests.exceptions.RequestException, ValueError, Exception) as e:
            print(f"Error during execution or processing for {self.meta.version}: {e}")
            return None

    @staticmethod
    def _parse_gradio_result(result: Any) -> Union[str, None]:
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, dict) and 'url' in first_item:
                return first_item['url']
            elif isinstance(first_item, str):
                return first_item
        elif isinstance(result, dict) and 'url' in result:
            return result['url']
        elif isinstance(result, str):
            return result
        return None

    @staticmethod
    def _process_result(image_url):
        print(f"Downloading image from: {image_url}")
        try:
            if not image_url.startswith(('http://', 'https://')):
                raise ValueError(f"Received path instead of URL: {image_url}. Cannot download directly.")

            response = requests.get(image_url, stream=True, timeout=60)
            response.raise_for_status()
            image_data = io.BytesIO(response.content)
            image_data.seek(0)
            return image_data
        except requests.exceptions.RequestException as e:
            print(f"Failed to download image from {image_url}: {e}")
            raise
        except ValueError as e:
            print(f"Error processing image URL: {e}")
            raise

    async def _use_backup(self, prompt: str) -> io.BytesIO:
        raise NotImplementedError("Backup mechanism not implemented in the base class.")


@register_model()
class FluxSchnellModel(FluxGradioBaseModel):
    def __init__(self):
        default_params = {
            "seed": 0,
            "randomize_seed": True,
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 4,
            "api_name": "/infer"
        }
        super().__init__(
            gradio_space_id="black-forest-labs/FLUX.1-schnell",
            model_version="FLUX.1-schnell",
            description="быстрая модель FLUX.1-schnell для генерации картинок",
            default_predict_params=default_params
        )
        self.backup_gradio_space_id = "lalashechka/FLUX_1"
        self.backup_api_name = "/predict"

    async def _use_backup(self, prompt: str) -> BytesIO | None:
        print(f"Using backup space: {self.backup_gradio_space_id}")
        try:
            backup_client = Client(self.backup_gradio_space_id, download_files=False)
            result = backup_client.predict(
                prompt=prompt,
            )
            image_url = self._parse_gradio_result(result)
            if not image_url:
                print(f"Could not extract image URL/path from backup Gradio result: {result}")
                return None

            return self._process_result(image_url)
        except Exception as e:
            print(f"Error during backup execution for {self.backup_gradio_space_id}: {e}")
            return None
