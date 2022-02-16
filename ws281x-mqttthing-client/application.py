import json
import logging
import os
import math

import paho.mqtt.client as mqtt
from rpi_ws281x import Color, PixelStrip

# Misc configuration
MQTT_HOSTNAME = "192.168.1.106"
SET_RGB_TOPIC = "rpi-0-w/tv-ambilight/setRGB"
GET_RGB_TOPIC = "rpi-0-w/tv-ambilight/getRGB"
GET_ON_TOPIC = "rpi-0-w/tv-ambilight/getOn"
SET_ON_TOPIC = "rpi-0-w/tv-ambilight/setOn"
GET_CT_TOPIC = "rpi-0-w/tv-ambilight/getCT"
SET_CT_TOPIC = "rpi-0-w/tv-ambilight/setCT"
STARTUP_TOPIC = "rpi-0-w/tv-ambilight/startup"
PAYLOAD_ENCODING = "utf-8"
STATE_FILE_NAME = "state.json"
ON_TOPIC_LIGHT_ON = "true"
ON_TOPIC_LIGHT_OFF = "false"

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

# Variables
strip = None
client = None
ingore_set_color_msg = False


def apply_color(r: str, g: str, b: str):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(int(r), int(g), int(b)))
    strip.show()


def publish_rgb_msg(r: int, g: int, b: int):
    payload = str(r) + "," + str(g) + "," + str(b)
    logging.debug("Sending GetRGB: " + payload)
    client.publish(GET_RGB_TOPIC, payload)


def publish_on_msg(payload: str):
    logging.debug("Sending GetON: " + payload)
    client.publish(GET_ON_TOPIC, payload)


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


def apply_state(state):
    if state[STATE_KEY_ON]:
        apply_color(state[STATE_KEY_R], state[STATE_KEY_G], state[STATE_KEY_B])
    else:
        apply_color(0, 0, 0)


def publish_state(state):
    if state[STATE_KEY_ON]:
        publish_on_msg(ON_TOPIC_LIGHT_ON)
        publish_rgb_msg(state[STATE_KEY_R], state[STATE_KEY_G], state[STATE_KEY_B])
    else:
        publish_on_msg(ON_TOPIC_LIGHT_OFF)


def on_connect(client, userdata, flags, rc):
    logging.info("Connected to MQTT server with result code: " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(SET_RGB_TOPIC)
    client.subscribe(SET_ON_TOPIC)
    client.subscribe(SET_CT_TOPIC)
    client.subscribe(STARTUP_TOPIC)
    publish_state(read_state())


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global ingore_set_color_msg
    if msg.topic == STARTUP_TOPIC:
        logging.debug("Received Stratup: " + str(msg.payload))
        ingore_set_color_msg = True

    if msg.topic == SET_ON_TOPIC:
        logging.debug("Received SetON: " + str(msg.payload))
        payload = msg.payload.decode(PAYLOAD_ENCODING)
        state = read_state()
        state[STATE_KEY_ON] = payload == ON_TOPIC_LIGHT_ON
        apply_state(state)
        write_state(state)
        publish_state(state)

    if msg.topic == SET_CT_TOPIC:
        logging.debug("Received SetCT: " + str(msg.payload))
        state = read_state()
        if not ingore_set_color_msg:
            ct_mired = msg.payload.decode(PAYLOAD_ENCODING)
            ct_kelvin = int(1000000 / int(ct_mired))
            logging.debug("Kelvin: " + str(ct_kelvin))
            (r, g, b) = convert_K_to_RGB(ct_kelvin)
            logging.debug("Applying CT " + str(ct_kelvin) + "K as " + str(r) + "," + str(g) + "," + str(b))
            if r == 0 and g == 0 and b == 0:
                state[STATE_KEY_ON] = False
            else:
                state[STATE_KEY_ON] = True
                state[STATE_KEY_R] = r
                state[STATE_KEY_G] = g
                state[STATE_KEY_B] = b
        else:
            logging.info("SetCT message ignored")
            ingore_set_color_msg = False
        apply_state(state)
        write_state(state)
        publish_state(state)

    if msg.topic == SET_RGB_TOPIC:
        logging.debug("Received SetRGB: " + str(msg.payload))
        state = read_state()
        if not ingore_set_color_msg:
            color_components = msg.payload.decode(PAYLOAD_ENCODING).split(",")
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
        else:
            logging.info("SetRGB message ignored")
            ingore_set_color_msg = False
        apply_state(state)
        write_state(state)
        publish_state(state)

def convert_K_to_RGB(colour_temperature):
    """
    Converts from K to RGB, algorithm courtesy of 
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    #range check
    if colour_temperature < 1000: 
        colour_temperature = 1000
    elif colour_temperature > 40000:
        colour_temperature = 40000
    
    tmp_internal = colour_temperature / 100.0
    
    # red 
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red
    
    # green
    if tmp_internal <=66:
        tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    
    # blue
    if tmp_internal >=66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue
    
    return red, green, blue

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s][%(processName)s][%(threadName)s][%(name)s] %(levelname)5s: %(message)s',
                        filename='application.log', encoding='utf-8', level=logging.DEBUG)

    logging.info("Application Start")
    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
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
