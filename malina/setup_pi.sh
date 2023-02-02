#!/bin/bash
sudo apt install git -y
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install i2c-tools -y
python -m ensurepip
sudo apt-get install python3-pip -y
pip install adafruit-charlcd
pip install git+https://github.com/chrisb2/pi_ina219.git
pip install smbus
