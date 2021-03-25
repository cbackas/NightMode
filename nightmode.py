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


def main():
    # connect to websocket server
    ws = websocket.WebSocket()
    ws.connect(ws_url)

    # get led controller instance
    led = LEDController()

    # Infinite loop waiting for WebSocket data
    while True:
        handle_messages(ws, led)


def handle_messages(ws, led):
    # wait for new message
    msg = ws.recv()

    # convert to json
    json_msg = json.loads(msg)

    # handle different message types
    msg_type = json_msg['type']
    if msg_type == 'event':
        handle_event(json_msg, led)
    elif msg_type == 'auth_required':
        print('Auth required.... sending token')
        send_auth(ws)
    elif msg_type == 'auth_ok':
        print('Authenticated')
        send_event_subscription(ws)
    elif msg_type == 'auth_invalid':
        print('Auth Failed: ' + json_msg['message'])
    elif msg_type == 'result':
        if json_msg['success']:
            print('Successfully subscribed to state_change events')
        else:
            print('Failed to subscribe to state_change events')
    else:
        print(msg)


# class instance that starts and stops nightmode
class LEDController:
    # init logi led DLL and turn lights off
    def enable_nightmode(self):
        logi_led.logi_led_init()
        time.sleep(1)
        logi_led.logi_led_set_lighting(0, 0, 0)

    # shut down the logi led DLL returning lights to normal
    def disable_nightmode(self):
        logi_led.logi_led_shutdown()


# handle state_change events
# filter out non monitor power related events
# set keyboard led's to corrispond with monitor power state
def handle_event(json_msg, led):
    entity_id = json_msg['event']['data']['entity_id']
    if entity_id == ha_monitored_entity_id:
        state = json_msg['event']['data']['new_state']['state']
        if state == 'on':
            led.disable_nightmode()
        elif state == 'off':
            led.enable_nightmode()
        print('Monitor Power State Updated: Nightmode ' + state)


# send a py dict (frame) as json to the socket server
def send_frame(ws, frame):
    json_string = json.dumps(frame)
    ws.send(json_string)


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


# execution starts here
main()