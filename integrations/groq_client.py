import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def ask_groq(prompt, previous_messages=[], model="openai/gpt-oss-20b"):

    response = client.chat.completions.create(
        model=model,
        messages=previous_messages + [{
            "role": "user",
            "content": prompt
        }]
    )

    return response.choices[0].message.content