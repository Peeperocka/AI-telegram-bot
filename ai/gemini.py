import os
from io import BytesIO

from google.genai import types
from PIL import Image
from dotenv import load_dotenv
from google import genai


def text_to_img_request(prompt: str) -> BytesIO | None:
    gemini_apikey = os.environ["GEMINI_APIKEY"]
    client = genai.Client(api_key=gemini_apikey)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return BytesIO(part.inline_data.data)
        return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def text_to_text_request(prompt: str) -> str:
    gemini_apikey = os.environ["GEMINI_APIKEY"]
    client = genai.Client(api_key=gemini_apikey)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error generating text: {e}")
        return f"Error: Could not generate text (Gemini).  Please try again later."


def main():
    load_dotenv()


if __name__ == '__main__':
    main()
