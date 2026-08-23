import json
import websocket
from config import printer_host

api_port = 7125
ws_url = "ws://%s:%s/websocket?token=" % ( printer_host, str(api_port))

objects = {
    "print_stats": None,
    "toolhead": ["homed_axes"],
    "display_status": ["progress"]
    }

def on_close(ws, close_status, close_msg):
    pass

def on_error(ws, error):
    print('Websocket error: %s' % error)

def on_message(ws, msg):
    response = json.loads(msg)

    if response['method'] ==  'notify_status_update':
        print(json.dumps(response, indent=2))

def on_open(ws):
    global objects
    print('on_open()...')

    #Unsubscribe from any printer objects
    d = {
        "jsonrpc": "2.0",
        "method": "printer.objects.subscribe",
        "params": {
            "objects": {

            }
        },
        "id": 3738
    }

    ws.send(json.dumps(d))

    data = {
        "jsonrpc": "2.0",
        "method": "printer.objects.query",
        "params": {
            "objects": objects
        },
        "id": 4654
    }

    # Subscribe to those objects
    ws.send(json.dumps(d))

ws = websocket.WebSocketApp(url=ws_url, on_close=on_close, on_error=on_error, on_message=on_message, on_open=on_open)
ws.run_forever()