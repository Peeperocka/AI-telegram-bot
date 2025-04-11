import gradio_client.exceptions
from gradio_client import Client
import io
import requests
from PIL import Image


def generate_schnell_backup(user_message: str) -> Image.Image:
    """Работает медленнее, но куда более отказоустойчивая"""
    client = Client(
        "lalashechka/FLUX_1",
        download_files=False
    )
    result = client.predict(
        prompt=user_message,
    )
    image_url = result['url']
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content))
    return image


def generate_schnell(user_message: str) -> Image.Image:
    client = Client(
        "black-forest-labs/FLUX.1-schnell",
        download_files=False
    )
    try:
        result = client.predict(
            prompt=user_message,
            seed=0,
            randomize_seed=True,
            width=1024,
            height=1024,
            num_inference_steps=4,
            api_name="/infer"
        )
        image_url = result[0]['url']
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        return image
    except gradio_client.exceptions.AppError as e:
        print(e)
        return generate_schnell_backup(user_message)
