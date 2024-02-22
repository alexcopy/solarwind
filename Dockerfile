# Use the official Raspberry Pi OS as the base image
FROM arm32v7/python:3.10-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Install build dependencies, I2C tools, and other required system libraries
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev libffi-dev python3-dev i2c-tools libyaml-dev



# Copy the requirements file into the container at /app
COPY requirements.txt /app/
#pip3 install python-doten
#pip3 install tuya-connector-python
# Install any dependencies
# Install dependencies from pyproject.toml
#RUN pip install --upgrade pip && \
#    pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Specify the command to run on container start

