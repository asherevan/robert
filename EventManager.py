### The event manager for the system. If any of the inputs change by a threshold, an event will be sent here via /submit. This program's job is to listen for events and when they occur, process them (add what occured and the needed information but cut out the rest) and pass it on to the AI model context manager.

from flask import Flask, request
import json
import threading
import time
from deepdiff import DeepDiff
import datetime

app = Flask(__name__)

def log(name, params):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f = open('eventLog.log', 'a')
    c = ''
    c += t + ' ' + name + ' {\n'
    for p in params:
        c += '    ' + p + ': ' + str(params[p]) + '\n'
    c += '}\n\n'
    print(c)
    f.write(c)
    f.close()

@app.route('/')
def test():
    return "Event server is working correctly!"

@app.route('/submit', methods=['POST'])
def recieve_json():
    j = request.args.get('event')
    if j is not None:
        event = {}
        event['reason'] = j['name']
        # I NEED AI TO WRITE THIS FOR ME :( :( :( :( :(

        j = json.loads(j)
        name = j.pop('name')
        log(name, j)

        return 'OK'
    else:
        return 'No JSON found in request!'
    

def assemble_context(ws):
    pass