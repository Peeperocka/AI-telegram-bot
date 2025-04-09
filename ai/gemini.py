import os
from io import BytesIO

from google.genai import types
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


def process_image_and_text(image_bytes: BytesIO, prompt: str) -> str:
    gemini_apikey = os.environ["GEMINI_APIKEY"]
    client = genai.Client(api_key=gemini_apikey)

    try:
        image_part = types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes.getvalue()))
        text_part = prompt

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[image_part, text_part]
        )
        return response.text
    except Exception as e:
        print(f"Error processing image and text: {e}")
        return f"Error: Could not process image and text (Gemini). Please try again later."


def audio_to_text_request(audio_bytes: BytesIO) -> str:
    gemini_apikey = os.environ["GEMINI_APIKEY"]
    client = genai.Client(api_key=gemini_apikey)

    try:
        audio_part = types.Part(inline_data=types.Blob(mime_type="audio/mpeg", data=audio_bytes.getvalue()))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[audio_part]
        )
        return response.text
    except Exception as e:
        print(f"Error processing audio: {e}")
        return f"Error: Could not process audio (Gemini). Please try again later."


def main():
    load_dotenv()


if __name__ == '__main__':
    main()
