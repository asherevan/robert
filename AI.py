# This file's responsibility is to assemble the information given such as the system prompt, personality file, and needed world state information, into a usable prompt then send it to the AI.

import os
from groq import Groq
from dotenv import load_dotenv
from config import model
from flask import Flask, request
from threading import Thread
from queue import Queue
import json
import time
import requests

app = Flask(__name__)

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

sysprompt = open('identity/systemcoreprompt.txt', 'r').read()
personality = open('identity/personality.txt', 'r').read()

system_prompt = [
    {
        'role': 'system',
        'content': sysprompt
    },
#    {
#        'role': 'system',
#        'content': personality
#    }
]

event_queue = Queue()

waiting_events_queue = Queue()

world_state = {}

tools = []

message_history = []

@app.route('/')
def test():
    return 'AI is working correctly!'

@app.route('/submit', methods=['POST'])
def event():
    event = request.get_json()
    print('Recieved event: ', event)

    event_queue.put(event)

    return 'OK'

@app.route('/world_state', methods=['POST'])
def world_state_update():
    global world_state
    world_state = request.get_json()

    return 'OK'

@app.route('/tools', methods=['POST'])
def get_tools():
    global tools
    tools = request.get_json()
    return 'OK'

def ask_groq(prompt):
    messages = message_history + [{
        "role": "user",
        "content": prompt
    }]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=system_prompt + messages,
            tools=tools,
            tool_choice='auto',
            temperature=0.3,
            max_completion_tokens=512
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            message_history.extend(messages[len(message_history):])
            message_history.append(assistant_message.model_dump(exclude_none=True))
            print(response.choices[0])
            return assistant_message

        assistant_message_dict = assistant_message.model_dump(exclude_none=True)
        messages.append(assistant_message_dict)

        for tool_call in tool_calls:
            tool_arguments = json.loads(tool_call.function.arguments or '{}')
            tool_response = requests.post(
                'http://127.0.0.1:5002/run',
                json={
                    'name': tool_call.function.name,
                    'args': tool_arguments
                },
                timeout=10
            )
            tool_response.raise_for_status()
            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': tool_response.text
            })

def process_immediately(event):
    global waiting_events_queue
    other_events = []

    for i in range(waiting_events_queue.qsize()):
        other_events.append(waiting_events_queue.get())

    context = {
        'event': event,

        'world_state': world_state,

        'other_events': other_events
    }

    context = json.dumps(context)

    ask_groq(context)

    waiting_events_queue = Queue() # Clear the queue

def process_event(event):
    if event['priority'] == 'high':
        process_immediately(event)
        time.sleep(5) # Temporary minimum interval

    else:
        waiting_events_queue.put(event)


def event_process_queue():
    while True:
        event = event_queue.get()

        process_event(event)

if __name__ == '__main__':
    Thread(target=event_process_queue).start()
    app.run(port=5001)