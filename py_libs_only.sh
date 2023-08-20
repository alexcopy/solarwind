#!/bin/bash
sudo apt-get install build-essential
sudo apt-get install i2c-tools -y
sudo apt-get install python3-pip -y
sudo chmod g+rw /dev/i2c-3
sudo apt install python3-dev python3-pip python3-setuptools -y
sudo apt install libffi-dev libssl-dev -y
pip3 install adafruit-charlcd
pip3 install git+https://github.com/chrisb2/pi_ina219.git
pip3 install smbus
sudo apt-get install screen -y
pip3 install python-dotenv
pip3 install apscheduler
pip3 install tuya-iot-py-sdk
pip3 install PyYAML
pip install python_weather