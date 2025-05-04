import os
from io import BytesIO
from typing import Union
from google.genai import types
from google import genai
from registry import (TextToTextModel, TextToImgModel,
                      ImgToTextModel, AudioToTextModel,
                      register_model, ModelInfo, BaseAIModel)


class GeminiBaseModel(BaseAIModel):
    provider = "Gemini"
    client = None

    def __init__(self, model_version: str, description: str, capabilities: tuple):
        if not GeminiBaseModel.client:
            GeminiBaseModel.client = genai.Client(api_key=os.environ["GEMINI_APIKEY"])

        self.meta = ModelInfo(
            provider=self.provider,
            version=model_version,
            description=description,
            capabilities=capabilities,
            is_async=False
        )

    async def execute(self, input_data: Union[str, BytesIO], prompt: str = None, enforce_text_response: bool = False) -> \
            Union[str, BytesIO, None]:
        if isinstance(input_data, str):
            if TextToImgModel in self.meta.capabilities and not enforce_text_response:
                return await self._generate_content(prompt=input_data, modalities=['Image', 'Text'])
            return await self._generate_text(prompt=input_data)

        if isinstance(input_data, BytesIO):
            if prompt is not None and ImgToTextModel in self.meta.capabilities:
                if prompt == "":
                    return "❗ Пожалуйста, добавьте текстовый запрос в подписи к изображению."
                return await self._process_image_with_prompt(image=input_data, prompt=prompt)
            if AudioToTextModel in self.meta.capabilities:
                return await self._process_audio(audio=input_data)
        return None

    async def _generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.meta.version,
            contents=prompt
        )
        return response.text

    async def _generate_content(self, prompt: str, modalities: list) -> Union[BytesIO, str, None]:
        try:
            response = self.client.models.generate_content(
                model=self.meta.version,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    response_modalities=modalities
                )
            )

            if not response.candidates:
                return None

            content = response.candidates[0].content
            return self._parse_response(content)

        except Exception as e:
            print(f"Error in content generation: {str(e)}")
            return None

    @staticmethod
    def _parse_response(content) -> Union[BytesIO, str, None]:
        text_response = None
        image_data = None

        for part in content.parts:
            if part.text:
                text_response = part.text.strip()
            if part.inline_data and "image/" in part.inline_data.mime_type:
                image_data = BytesIO(part.inline_data.data)

        return image_data or text_response or None

    async def _process_image_with_prompt(self, image: BytesIO, prompt: str) -> str:
        image_part = types.Part(inline_data=types.Blob(
            mime_type="image/jpeg",
            data=image.getvalue()
        ))
        response = self.client.models.generate_content(
            model=self.meta.version,
            contents=[image_part, prompt]
        )
        return response.text

    async def _process_audio(self, audio: BytesIO) -> str:
        audio_part = types.Part(inline_data=types.Blob(
            mime_type="audio/mpeg",
            data=audio.getvalue()
        ))
        response = self.client.models.generate_content(
            model=self.meta.version,
            contents=[audio_part]
        )
        return response.text


@register_model()
class GeminiFlash(GeminiBaseModel):
    def __init__(self):
        super().__init__(
            model_version="gemini-2.0-flash-exp-image-generation",
            description="быстро работающая модель, поддерживающая генерацию картинок",
            capabilities=(
                TextToTextModel,
                TextToImgModel,
                ImgToTextModel,
                AudioToTextModel
            )
        )


@register_model()
class GeminiPro(GeminiBaseModel):
    def __init__(self):
        super().__init__(
            model_version="gemini-1.5-pro",
            description="продвинутая модель gemini, способная к более точному анализу",
            capabilities=(TextToTextModel,)
        )


@register_model()
class GeminiFlashLite(GeminiBaseModel):
    def __init__(self):
        super().__init__(
            model_version="gemini-2.0-flash-lite",
            description="облегченная и быстрая модель Gemini, оптимизированная для скорости и эффективности.",
            capabilities=(TextToTextModel, ImgToTextModel, AudioToTextModel,)
        )


@register_model()
class GeminiFlashOld(GeminiBaseModel):
    def __init__(self):
        super().__init__(
            model_version="gemini-1.5-flash",
            description="более ранняя версия Gemini Flash, с балансом скорости и возможностей.",
            capabilities=(TextToTextModel, ImgToTextModel, AudioToTextModel)
        )


@register_model()
class GeminiFlashOldLite(GeminiBaseModel):
    def __init__(self):
        super().__init__(
            model_version="gemini-1.5-flash-8b",
            description="самая легкая и старая Gemini Flash для задач с ограниченными ресурсами.",
            capabilities=(TextToTextModel, ImgToTextModel, AudioToTextModel)
        )
