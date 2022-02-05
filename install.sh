#!/bin/bash

set -e
set -x

RpiHostname="192.168.1.108"

scp -r "ws281x-mqttthing-client" pi@$RpiHostname:~
ssh "pi@$RpiHostname" "sudo systemctl stop ws281x-mqttthing-client.service; sudo mv ~/ws281x-mqttthing-client/ws281x-mqttthing-client.service /lib/systemd/system && sudo chmod 644 /lib/systemd/system/ws281x-mqttthing-client.service && sudo systemctl daemon-reload && sudo systemctl enable ws281x-mqttthing-client.service && sudo systemctl start ws281x-mqttthing-client.service"
