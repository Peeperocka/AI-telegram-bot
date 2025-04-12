from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Type, Dict, List, Optional, ClassVar, Any


class BaseAIModel(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        self.meta: ClassVar['ModelInfo'] = Any

    @abstractmethod
    async def execute(self, *args, **kwargs):
        pass


async def get_available_models(model_type: Type[BaseAIModel]) -> dict[str, str]:
    registry = AIRegistry()
    models = {}

    print(registry.get_models_by_type(model_type))
    for model in registry.get_models_by_type(model_type):
        model_id = f"{model.meta.provider.lower()}:{model.meta.version}"
        display_name = f"{model.meta.provider} {model.meta.version}"

        models[model_id] = display_name

    return models


@dataclass
class ModelInfo:
    provider: str
    version: str
    description: str
    capabilities: List[Type[BaseAIModel]]
    is_async: bool
    default: bool = False
    is_available_to_user: bool = True


class TextToTextModel(BaseAIModel):
    """Текст -> Текст"""


class TextToImgModel(BaseAIModel):
    """Текст -> Изображение"""


class ImgToTextModel(BaseAIModel):
    """Изображение -> Текст"""


class AudioToTextModel(BaseAIModel):
    """Аудио -> Текст"""


class AIRegistry:
    _instance = None
    _providers: Dict[str, Dict[str, BaseAIModel]] = defaultdict(dict)  # {provider: {version: model}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = defaultdict(dict)
        return cls._instance

    def add_model(self, model: BaseAIModel) -> None:
        if not hasattr(model, 'meta'):
            raise ValueError("Model must have meta attribute")

        provider = model.meta.provider.lower()
        version = model.meta.version

        if version in self._providers[provider]:
            raise ValueError(f"Model {provider}:{version} already exists")

        self._providers[provider][version] = model
        print(f"Registered: {provider} {version}")

    def get_model(self, provider: str, version: str) -> Optional[BaseAIModel]:
        return self._providers.get(provider.lower(), {}).get(version)

    def get_default_model(self, provider: str) -> Optional[BaseAIModel]:
        models = self._providers.get(provider.lower(), {})
        for model in models.values():
            if model.meta.default:
                return model
        return next(iter(models.values()), None) if models else None

    def get_providers(self) -> List[str]:
        return list(self._providers.keys())

    def get_providers_to_user(self) -> List[str]:
        return list(provider for provider in self._providers.keys() if provider != "whisper")

    def get_all_models(self) -> List[BaseAIModel]:
        return [model for versions in self._providers.values() for model in versions.values()]

    def get_models_for_provider(self, provider: str) -> List[BaseAIModel]:
        return list(self._providers.get(provider.lower(), {}).values())


def register_model(*categories: Type[BaseAIModel]):
    def decorator(cls):
        instance = cls()
        registry = AIRegistry()
        registry.add_model(instance)
        return cls

    return decorator
