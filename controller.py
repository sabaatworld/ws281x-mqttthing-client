import json
import os

import paho.mqtt.client as mqtt
from rpi_ws281x import Color, PixelStrip

# Misc configuration
MQTT_HOSTNAME = "192.168.1.106"
SET_RGB_TOPIC = "rpi-0-w/tv-ambilight/setRGB"
GET_RGB_TOPIC = "rpi-0-w/tv-ambilight/getRGB"
GET_ON_TOPIC = "rpi-0-w/tv-ambilight/getOn"
SET_ON_TOPIC = "rpi-0-w/tv-ambilight/setOn"
PAYLOAD_ENCODING = "utf-8"
STATE_FILE_NAME = "controller_state.json"

STATE_KEY_ON = 'on'
STATE_KEY_R = 'r'
STATE_KEY_G = 'g'
STATE_KEY_B = 'b'

# LED strip configuration
LED_COUNT = 185
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

strip = None
client = None


def write_state(state):
    with open(STATE_FILE_NAME, 'w') as state_file:
        state_file.write(json.dumps(state))


def read_state():
    if os.path.exists(STATE_FILE_NAME):
        with open(STATE_FILE_NAME, 'r') as state_file:
            return json.loads(state_file.read())
    else:
        default_state = {
            STATE_KEY_ON: True,
            STATE_KEY_R: 255,
            STATE_KEY_G: 255,
            STATE_KEY_B: 255
        }
        write_state(default_state)
        return default_state


def apply_color(r, g, b):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(int(r), int(g), int(b)))
    strip.show()


def publish_rgb_msg(r, g, b):
    payload = str(r) + "," + str(g) + "," + str(b)
    print("Sending GetRGB: " + payload)
    client.publish(GET_RGB_TOPIC, payload)


def publish_on_msg(payload):
    print("Sending GetON: " + str(payload))
    client.publish(GET_ON_TOPIC, payload)


def apply_state(state):
    if state[STATE_KEY_ON]:
        apply_color(state[STATE_KEY_R], state[STATE_KEY_G], state[STATE_KEY_B])
    else:
        apply_color(0, 0, 0)


def publish_state(state):
    if state[STATE_KEY_ON]:
        publish_rgb_msg(state[STATE_KEY_R],
                        state[STATE_KEY_G], state[STATE_KEY_B])
    else:
        publish_on_msg("false")


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT server with result code: " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(SET_RGB_TOPIC)
    client.subscribe(SET_ON_TOPIC)
    publish_state(read_state())


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if msg.topic == SET_ON_TOPIC:
        print("Received SetON: " + str(msg.payload))
        payload = msg.payload.decode(PAYLOAD_ENCODING)
        state = read_state()
        state[STATE_KEY_ON] = payload == "true"
        apply_state(state)
        write_state(state)
        publish_on_msg(payload)

    if msg.topic == SET_RGB_TOPIC:
        print("Received SetRGB: " + str(msg.payload))
        color_components = msg.payload.decode(PAYLOAD_ENCODING).split(",")
        state = read_state()
        r = int(color_components[0])
        g = int(color_components[1])
        b = int(color_components[2])
        if r == 0 and g == 0 and b == 0:
            state[STATE_KEY_ON] = False
        else:
            state[STATE_KEY_ON] = True
            state[STATE_KEY_R] = r
            state[STATE_KEY_G] = g
            state[STATE_KEY_B] = b
        apply_state(state)
        write_state(state)
        if r == 0 and g == 0 and b == 0:
            publish_on_msg("false")
        else:
            publish_rgb_msg(state[STATE_KEY_R],
                            state[STATE_KEY_G], state[STATE_KEY_B])


if __name__ == '__main__':
    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                       LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Initialize the library (must be called once before other functions).
    strip.begin()
    # Wipe on init.
    state = read_state()
    apply_state(state)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOSTNAME)
    # Retry all connection attempts including the first one.
    client.loop_forever(1.0, 1, True)
