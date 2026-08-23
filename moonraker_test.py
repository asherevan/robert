import json
from websocket import create_connection

printer_ip = "192.168.0.84"
api_port = 7125
ws_url = "ws://%s:%s/websocket?token=" % ( printer_ip, str(api_port))

ws = create_connection(ws_url)

data = {
    "jsonrpc": "2.0",
    "method": "printer.objects.query",
    "params": {
        "objects": {
            "print_stats": None,
            "toolhead": ["homed_axes"],
            "display_status": ["progress"]
        }
    },
    "id": 4654
  }

ws.send(json.dumps(data))

response = json.loads(ws.recv())

# Moonraker sends cyclic status information over the websocket, we need to make sure that
# the response data for our request was received.
# Cyclic status data doesn't contain an 'id' field.

while not 'id' in response:
    response = json.loads(ws.recv())

print(json.dumps(response, indent=2))

ws.close()