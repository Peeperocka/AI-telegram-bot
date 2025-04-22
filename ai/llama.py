from groq import Groq
import os
from registry import TextToTextModel, register_model, ModelInfo, BaseAIModel


class LlamaBaseModel(BaseAIModel):
    provider = "Llama"
    client = None

    def __init__(self, model_version: str, description: str):
        if not LlamaBaseModel.client:
            LlamaBaseModel.client = Groq(api_key=os.environ["GROQ_APIKEY"])

        self.meta = ModelInfo(
            provider=self.provider,
            version=model_version,
            description=description,
            capabilities=(TextToTextModel,),
            is_async=False
        )

    async def execute(self, prompt: str) -> str | None:
        try:
            completion = self.client.chat.completions.create(
                model=self.meta.version,
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_tokens=1024
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(e)
            return None


@register_model()
class Llama3_1_8B(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama-3.1-8b-instant",
            description="быстрая 8B модель Llama 3.1 с низкой задержкой"
        )


@register_model()
class Llama3_1_70B_versatile(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama-3.3-70b-versatile",
            description="мощная и универсальная 70B модель Llama"
        )


@register_model()
class Llama3_8B_8192(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama3-8b-8192",
            description="быстрая 8B модель Llama 3 с контекстным окном 8192 токенов"
        )


@register_model()
class Llama3_70B_8192(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama3-70b-8192",
            description="мощная 70B модель Llama 3 с контекстным окном 8192 токенов"
        )
