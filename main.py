# This program's roles are:
# - Start each of the induvidual programs that make up Robert
# - Monitor and restart those if they fail
# - Log any errors that don't get caught
# - Host the debug console

import subprocess
import os
import threading
import time
import requests

def input_loop(delay_time, function):
    while True:
        try:
            result = function()
            print(f'Ran {function.__module__}')
        except Exception as e:
            result = {function.__module__: str(e)}

        try:
            print(result)
            request = requests.post('http://127.0.0.1:5000/set?name='+result['name']+'&value='+str(result['value']), timeout=3)
            print(request)
        except:
            pass
        time.sleep(delay_time)

startup_commands = [
#    'flask --app InputManager.py run --host=0.0.0.0 --port 5000',
    'flask --app EventManager.py run --host=0.0.0.0 --port 5001',
]

# Split up each of the commands into the separate parts for later
for i in startup_commands:
    startup_commands[i] = i.split(' ')

# Run each of the commands
for c in startup_commands:
    command_full = ' '.join(c)
    print(f'Running {command_full}')
    subprocess.Popen(c)

modules = os.listdir('sources')
modules.pop(modules.index('__pycache__'))

for i in modules:
    exec('import sources.'+ i.strip(".py") +' as source') # Import the module by name
    threading.Thread(target=input_loop, args=(source.interval, source.get)).start()