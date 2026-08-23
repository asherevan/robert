from flask import Flask, request
import os
import requests
from threading import Thread
import importlib

app = Flask(__name__)

tools = {}

@app.route('/')
def index():
    return 'ToolManager functioning!'

@app.route('/run', methods=['GET', 'POST'])
def run_tool():
    j = request.get_json(silent=True) or request.args.to_dict()
    try:
        args = j.get('args', {})
        if isinstance(args, str):
            import json
            args = json.loads(args)
        return str(tools[j['name']][0](**args))
    except Exception as e:
        return str(e), 400

@app.route('/tools', methods=['GET'])
def list_tools():
    return {'tools': list(tools.keys())}

def load_tools():
    d = [filename for filename in os.listdir('tools') if filename.endswith('.py') and filename != '__init__.py']

    for l in d:
        tool = importlib.import_module(f"tools.{l[:-3]}")
        tool_main = tool.main
        tool_schema = tool.function_schema

        tools[tool_schema['function']['name']] = (tool_main, tool_schema)

    requests.post(
        'http://127.0.0.1:5001/tools',
        json=[schema for _, schema in tools.values()],
        timeout=3
    )

if __name__ == '__main__':
    Thread(target=load_tools).start()

    app.run(port=5002)