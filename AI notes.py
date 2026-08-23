from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def add_two_numbers(a: int, b: int):
    "Add two numbers, a and b"

    return a + b

tools = {''}

message_history = []

prompt = {
    'role': 'user',
    'content': input(' > ')
}

response = client.chat.completions.create(
        model='openai/gpt-oss-20b',
        messages=message_history + prompt

    )


print(response.choices[0].message.content)