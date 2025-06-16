#!/bin/bash

# Install critical system dependencies
apt-get update && apt-get install -y \
    python3.9-distutils \
    python3.9-dev \
    libgl1 \
    libzbar0

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools first
pip install --upgrade pip setuptools==65.5.0 wheel

# Install Python packages
pip install -r requirements.txt

# Create required directories
mkdir -p /tmp/uploads
mkdir -p /tmp/static
