#!/bin/bash

# Set Python 3.9 explicitly
echo "python-3.9" > runtime.txt

# Install system dependencies ONLY for Python
apt-get update && apt-get install -y python3-distutils libzbar0

# Python package setup
python -m pip install --upgrade pip setuptools==65.5.0
pip install wheel
pip install -r requirements.txt

# Create required directories
mkdir -p /tmp/uploads
mkdir -p /tmp/static
