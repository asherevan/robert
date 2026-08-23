import requests
import time
from typing import Literal
from enum import Enum, IntEnum
import json

def send_event(source, type, data, priority: Literal['high', 'medium', 'low'] = 'medium'):

    if priority not in {'high', 'low', 'medium'}:
        raise ValueError(priority + ' is not a valid option for priority. Please choose from "high", "medium", or "low".')

    event = {
        "source": source,
        "type": type,
        "timestamp": time.time(),
        "data": data,
        "priority": priority,
    }

    try:
        requests.post(
            "http://127.0.0.1:5000/submit",
            json=event,
            timeout=0.5
        )
    except requests.Timeout:
        print('Request timed out!')

def send_input(param, value):
    try:
        requests.post(
            'http://127.0.0.1:5000/update',
            params={'name': param, 'value': value},
            timeout=0.5
        )
    except requests.Timeout:
        print('Request timed out!')