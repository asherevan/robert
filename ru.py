import logging
import requests
import time
from typing import Literal

logger = logging.getLogger(__name__)


def _safe_post(url, **kwargs):
    try:
        return requests.post(url, **kwargs)
    except requests.RequestException as exc:
        logger.warning("Request failed for %s: %s", url, exc)
        print(f"Request failed for {url}: {exc}")
        return None


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

    _safe_post(
        "http://127.0.0.1:5000/submit",
        json=event,
        timeout=0.5,
    )


def send_input(param, value):
    _safe_post(
        'http://127.0.0.1:5000/update',
        params={'name': param, 'value': value},
        timeout=0.5,
    )