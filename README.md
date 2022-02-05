# ws281x-mqttthing-client

Python code for controlling ws281x LED strip in Homebridge using [mqttthing](https://github.com/arachnetech/homebridge-mqttthing). It uses the [rpi-ws281x-python](https://github.com/rpi-ws281x/rpi-ws281x-python) library to control the light strip; which requires installation of [rpi_ws281x](https://github.com/richardghirst/rpi_ws281x) ([detailed instuctions](https://github.com/jgarff/rpi_ws281x)).

## Sample Homebridge Config

Here's a sample "Light bulb - RGB" configuration that is used in conjunction with this code to expose the RGB lightstrip to HomeKit.

```
{
    "type": "lightbulb-RGB",
    "name": "TV Ambilight",
    "mqttPubOptions": {
        "retain": false
    },
    "logMqtt": false,
    "optimizePublishing": false,
    "topics": {
        "getRGB": "rpi-0-w/tv-ambilight/getRGB",
        "setRGB": "rpi-0-w/tv-ambilight/setRGB",
        "getOn": "rpi-0-w/tv-ambilight/getOn",
        "setOn": "rpi-0-w/tv-ambilight/setOn"
    },
    "confirmationIndicateOffline": true,
    "accessory": "mqttthing"
}
```

## Useful Documentation

- Paho MQTT Documentation: https://pypi.org/project/paho-mqtt/
