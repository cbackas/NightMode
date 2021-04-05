#! python

from logipy import logi_led
import websocket
import json
import time

# home assistant socket server address
ws_url = 'ws://localhost:8123/api/websocket'
# home assistant auth token
# https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token
auth_token = ''
# entity id of home assistant device to tie LED state to
ha_monitored_entity_id = ''

last_id = 0
request_cache = []


def main():
    # get led controller instance and set to default state
    led = LEDController()
    led.default()

    # connect to websocket server
    ws = websocket.WebSocket()
    ws.connect(ws_url)
    print("Initializing websocket connection...")

    # Infinite loop waiting for WebSocket data
    while True:
        handle_messages(ws, led)


def handle_messages(ws, led):
    # wait for new message
    msg = ws.recv()

    # convert to json
    try:
        json_msg = json.loads(msg)
    except json.decoder.JSONDecodeError:
        print(f'Error decoding message to JSON: {msg}')
        return

    # handle different message types
    msg_type = json_msg['type']
    if msg_type == 'event':
        handle_event(json_msg, led)
    elif msg_type == 'auth_required':
        print('Auth required.... sending token')
        send_auth(ws)
    elif msg_type == 'auth_ok':
        print('Authenticated')
        # subscribe to state change events
        send_event_subscription(ws)
        # get initial states to properly set keyboard LEDs upon connection
        send_states_request(ws)
    elif msg_type == 'auth_invalid':
        print('Auth Failed: ' + json_msg['message'])
    elif msg_type == 'result':
        # compare the result ID to our cached requests in order to process the result correctly
        result_id = json_msg['id']
        origin_request = next(
            (item for item in request_cache if item['id'] == result_id), None)
        if origin_request:
            success = json_msg['success']
            origin_request_type = origin_request['type']
            if origin_request_type == 'subscribe_events':
                if success:
                    print('Successfully subscribed to state_change events')
                else:
                    print('Failed to subscribe to state_change events')
            elif origin_request_type == 'get_states':
                handle_all_states(json_msg, led)
    else:
        print(msg)


# class instance that starts and stops nightmode
class LEDController:
    # init logi led DLL and turn lights off
    def enable_nightmode(self):
        logi_led.logi_led_init()
        time.sleep(0.5)
        logi_led.logi_led_set_lighting(0, 0, 0)

    # shut down the logi led DLL returning lights to normal
    def disable_nightmode(self):
        logi_led.logi_led_shutdown()

    # defines default state
    def default(self):
        self.disable_nightmode()


# handle state_change events
# filter out non monitor power related events
# set keyboard led's to corrispond with monitor power state
def handle_event(json_msg, led):
    entity_id = json_msg['event']['data']['entity_id']
    if entity_id == ha_monitored_entity_id:
        state = json_msg['event']['data']['new_state']['state']
        handle_monitor_state(state, led)


# takes in a list of all HA states
# filter out non monitor power related events
# set keyboard led's to corrispond with monitor power state
def handle_all_states(json_msg, led):
    results = json_msg['result']
    monitor = next(
        (item
         for item in results if item['entity_id'] == ha_monitored_entity_id),
        None)
    if monitor:
        handle_monitor_state(monitor['state'], led)


# takes in monitor state (on, off, etc) and LED instance
# sets nightmode to the correct state with logging
def handle_monitor_state(state, led):
    if state in ['on', 'unavailable']:
        led.disable_nightmode()
        print('Monitor Power State Updated: Nightmode disabled')
    elif state == 'off':
        led.enable_nightmode()
        print('Monitor Power State Updated: Nightmode enabled')


# send a py dict (frame) as json to the socket server
def send_frame(ws, frame):
    json_string = json.dumps(frame)
    ws.send(json_string)

    # cache requests so the can be processed in context on return
    if (frame['type'] != 'auth'):
        request_cache.append(frame)


# send frame to authenticate
def send_auth(ws):
    auth_frame = {"type": "auth", "access_token": auth_token}
    send_frame(ws, auth_frame)


# send frame to subscribe to state_changed event notifications
def send_event_subscription(ws):
    global last_id
    last_id += 1
    sub_frame = {
        "id": last_id,
        "type": "subscribe_events",
        "event_type": "state_changed"
    }
    send_frame(ws, sub_frame)


# send frame to request all HA entity states
# needed to get initial state upon script start (or restart)
def send_states_request(ws):
    global last_id
    last_id += 1
    state_request_frame = {"id": last_id, "type": "get_states"}
    send_frame(ws, state_request_frame)


# execution starts here
# do some looping so errors can be caught and the execution of the whole script restarted
while True:
    try:
        main()
    except ConnectionError:
        print("Connection Error: Restarting script")
        time.sleep(5)
        continue
    except OSError:
        print("OSError: Restarting script")
        time.sleep(5)
        continue
