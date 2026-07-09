# We're going to ignore this for now because events are more important

from flask import Flask, request
import json
import requests
import threading
from deepdiff import DeepDiff
import time

app = Flask(__name__)

world_status = {}
recent_update = {}

medians_map = json.load(open('inputMedians.json', 'r'))

def save_json():
    f = open('worldStatus.json', 'w')
    j = json.dumps(world_status)
    f.write(j)
    f.close()

def send_event(j):
    requests.post(f'http://127.0.0.1:5001/submit?event={j}')

def str_to_time(ts) -> int:
    tm = 0
    dt, t = ts.split(' ')
    ye, mon, day = dt.split('-')
    hr, min, _ = t.split(':')
    tm += int(min)
    tm += int(hr) * 60
    tm += int(day) * 60 * 24
    tm += int(mon) * 60 * 24 * 31
    tm += int(ye) * 60 * 24 * 31 * 12
    return tm # Return the time in minutes


@app.route('/')
def test():
    return 'Input server functioning as intended!'

@app.route('/set', methods=['POST'])
def set_parameter():
    name = request.args.get('name')
    value = request.args.get('value')
    group = request.args.get('group')
    if group:
        if isinstance(type(world_status[group]), dict) and len(world_status[group]) > 0:
            recent_update[group][name] = value
        else:
            recent_update[group] = {}
            recent_update[group][name] = value
    else:
        recent_update[name] = value
    print(json.dumps(recent_update))

    return 'OK'

@app.route('/get')
def get_status():
    group = request.args.get('group')
    name = request.args.get('name')
    if group and not name:
        try:
            return json.dumps(world_status[group])
        except:
            return f'{group} was not found in the world state dictionary!'
    elif group and name:
        try:
            return json.dumps(world_status[group][name])
        except:
            return f'{group}.{name} was not found in the world state dictionary!'
    elif name and not group:
        try:
            return json.dumps(world_status[name])
        except:
            return f'{name} was not found in the world state dictionary'
    else:
        return 'Missing either the "group" or "name" parameters in the request!'

def process_thread():
    global world_status, recent_update

    while True:
        if world_status != recent_update:
            diffs = DeepDiff(world_status, recent_update)
            if len(diffs) > 0:
                diffs = diffs['values_changed']['root']

                for c in diffs['new_value']:
                    new = diffs['new_value'][c]
                    try:
                        old = diffs['old_value'][c]
                    except KeyError:
                        if type(new) == int:
                            old = 0
                        elif type(new) == str:
                            old = ''
                        elif type(new) == bool:
                            old = None
                        else:
                            old = None
                            print('Type '+str(type(new))+' is not yet implemented!')
                    median = medians_map[c]

                    if median['type'] == 'time':
                        diff = abs(str_to_time(old) - str_to_time(new))
                        if diff > median['median']:
                            send_event({'name': median['name']})

                world_status = recent_update # Reset it so that changes will still be detected on the next round


        time.sleep(0.25)


threading.Thread(target=process_thread).start()