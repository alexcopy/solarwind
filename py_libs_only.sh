#!/bin/bash
sudo apt-get install i2c-tools -y
sudo apt-get install python3-pip -y
pip3 install adafruit-charlcd
pip3 install git+https://github.com/chrisb2/pi_ina219.git
pip3 install smbus
sudo apt-get install screen -y
pip3 install python-dotenv
pip3 install apscheduler
pip3 install tuya-iot-py-sdk