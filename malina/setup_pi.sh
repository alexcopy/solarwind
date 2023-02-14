#!/bin/bash
sudo apt-mark hold libraspberrypi-bin libraspberrypi-dev libraspberrypi-doc libraspberrypi0
sudo apt-mark hold raspberrypi-bootloader raspberrypi-kernel raspberrypi-kernel-headers

sudo apt-get update && sudo apt-get upgrade -y
sudo apt install git -y
sudo apt-get install i2c-tools -y
cd /tmp || exit
wget https://www.python.org/ftp/python/3.10.9/Python-3.10.9.tgz
tar -zxvf Python-3.10.9.tgz
cd Python-3.10.9 || exit
./configure --enable-optimizations
sudo apt update
sudo apt install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo make altinstall
cd /usr/bin || exit
sudo rm python3
sudo ln -s /usr/local/bin/python3.10 python

sudo apt-get install python3-pip -y
sudo apt-get install screen -y

pip3 install smbus
pip3 install python-dotenv
pip3 install apscheduler
pip3 install tuya-iot-py-sdk
sudo install vim -y
python3 -m ensurepip
#if error then add .10 to begging of file /usr/bin/lsb_release
# !/usr/bin/python3.10 -Es
