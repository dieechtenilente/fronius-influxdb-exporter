FROM debian:trixie-slim

# Set environment variables to non-interactive (to avoid prompts during installation)
ENV DEBIAN_FRONTEND=noninteractive

# Update base image
RUN apt update && apt upgrade -y

# Install Python3 and PIP
RUN apt install -y python3-pip python3-venv python3-full && rm -rf /var/lib/apt/lists/* /usr/share/doc/* /usr/share/man/* /usr/share/locale/*

# Create fronius directory
RUN mkdir -p /opt/fronius-exporter

# Create venv and install requirements
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/fronius-exporter/venv && /opt/fronius-exporter/venv/bin/python -m pip install --no-cache-dir --upgrade pip && /opt/fronius-exporter/venv/bin/python -m pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY script.py /opt/fronius-exporter/script.py

ENTRYPOINT /opt/fronius-exporter/venv/bin/python /opt/fronius-exporter/script.py \
                        --froniusIP $FRONIUS_IP \
                        --plantName $PLANT_NAME \
                        --InfluxDBserver $INFLUXDB_SERVER \
                        --InfluxDBtoken $INFLUXDB_TOKEN \
                        --InfluxDBorg $INFLUXDB_ORG \
                        --InfluxDBbucket $INFLUXDB_BUCKET