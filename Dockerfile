# Use the official Raspberry Pi OS as the base image
FROM arm32v7/python:3.8-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Install I2C tools
RUN apt-get update && apt-get install -y \
    i2c-tools

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Specify the command to run on container start
CMD ["python", "main.py"]
