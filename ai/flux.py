from gradio_client import Client
import io
import requests
from PIL import Image


def generate_flux(user_message: str) -> Image.Image:
    client = Client(
        "lalashechka/FLUX_1",
        download_files=False
    )
    result = client.predict(
        prompt=user_message,
        task="FLUX.1 [schnell]",
    )
    image_url = result['url']
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content))
    return image
