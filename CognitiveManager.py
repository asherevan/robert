from flask import Flask, request
import json
import threading
import time
import datetime
import requests
from config import update_time, always_sent

world_state = {}

STALE_TIMEOUT = 1200 # Remove states from the world state after 20 minutes of not being updated

app = Flask(__name__)

def log(event):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f = open('eventLog.log', 'a')
    c = ''
    c += '[' + t + '] ' + event['type'] + ' {\n'
    c += '\tSource: ' + event['source'] + '\n'
    c += '\tData:\n'
    d = event['data']
    for i in d:
        c += '\t    ' + i + ': ' + str(d[i]) + '\n'
    c += '}'
    print(c)
    f.write(c)
    f.close()

@app.route('/')
def test():
    return "Cognitive Manager server is working correctly!"

@app.route('/submit', methods=['POST'])
def receive_event():
    e = request.get_json()
    if e is not None:
        print(e)
        log(e)

        requests.post('http://127.0.0.1:5001/submit', json=e, timeout=3)

        return 'OK'
    else:
        return 'No JSON found in request!'
    
@app.route('/update', methods=['POST'])
def update_param(): # Update a value in the world status dictionary to be fetched later
    name = request.args.get('name')
    value = request.args.get('value')

    world_state[name] = {'value':value, 'timestamp':time.time()}

    return 'OK'

@app.route('/get')
def get_param(): # Retrieve a value from the world status dictionary
    j = request.args.get('name')
    try:
        return str(world_state[j]['value'])
    except KeyError:
        return '"' + j + '" was not found in the world state.'
    
@app.route('/get_available')
def get_available():
    return str(list(world_state.keys()))

def stale_remove_thread():
    while True:
        k = list(world_state.keys())
        for i in k:
            t = world_state[i]['timestamp']
            if time.time() - t > STALE_TIMEOUT:
                print(f'{i} was stale. Removing from world status.')
                world_state.pop(i)
        time.sleep(5)

def timed_send_world_state():
    while True:
        time.sleep(update_time)

        to_be_sent = {}

        for i in always_sent:
            try:
                to_be_sent[i] = world_state[i]
            except KeyError:
                print('Always sent key "' + str(i) +'" is not currently available')

        requests.post('http://127.0.0.1:5001/world_state', json=to_be_sent)

if __name__ != 'CognitiveManager':
    threading.Thread(target=stale_remove_thread).start()
    threading.Thread(target=timed_send_world_state).start()
    app.run(host='127.0.0.1', port=5000)