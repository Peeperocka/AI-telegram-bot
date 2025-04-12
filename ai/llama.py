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
            capabilities=[TextToTextModel],
            is_async=False
        )

    async def execute(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.meta.version,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024
        )
        return completion.choices[0].message.content


@register_model(TextToTextModel)
class Llama3_8B(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama-3.1-8b-instant",
            description="Fast 8B parameter model"
        )


@register_model(TextToTextModel)
class Llama3_70B(LlamaBaseModel):
    def __init__(self):
        super().__init__(
            model_version="llama-3.1-70b-instant",
            description="Powerful 70B parameter model"
        )
