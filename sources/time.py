import datetime
import requests
import robertutils
import time

interval = 10

event_threshold = 60 * 30 # Every 30 minutes, send an event


old_now = time.time()

while True:
    now = time.time() # The time for comparison
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # The time in proper format

    robertutils.send_input('current_time', t) # Send the time as an input

    if now - old_now > event_threshold:
        old_now = now

    time.sleep(interval) # Wait <interval> seconds