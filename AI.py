# This file's responsibility is to assemble the information given such as the system prompt, personality file, and needed world state information, into a usable prompt then send it to the AI.

import os
from groq import Groq
from dotenv import load_dotenv
from config.config import model

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

sysprompt = open('identity/systemcoreprompt.txt', 'r').read()
personality = open('identity/personality.txt', 'r').read()

system_prompt = [
    {
        'role': 'system',
        'content': sysprompt + '\n' + personality
    }
]

def ask_groq(prompt, previous_messages=[]):
    message = [{
            "role": "user",
            "content": prompt
        }]
    response = client.chat.completions.create(
        model=model,
        messages=system_prompt + previous_messages + message
    )

    return response.choices[0].message.content