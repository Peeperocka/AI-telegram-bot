from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()


def text_request(user_message: str) -> str:
    GROQ_APIKEY = os.environ["GROQ_APIKEY"]
    client = Groq(
        api_key=GROQ_APIKEY,
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "you are a helpful assistant."
            },
            {
                "role": "user",
                "content": user_message,
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content
