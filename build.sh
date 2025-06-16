apt-get update && apt-get install -y \
    python3-distutils \
    libgl1 \
    libzbar0

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools

# Install Python packages
pip install -r requirements.txt

# Create required directories (Vercel needs explicit creation)
mkdir -p /tmp/uploads
mkdir -p /tmp/static
