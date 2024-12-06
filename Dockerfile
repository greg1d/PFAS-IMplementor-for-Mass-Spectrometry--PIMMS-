FROM continuumio/miniconda3

# Install system packages including debugging tools and VNC server
RUN apt-get update && apt-get install -y \
    python3-tk \
    bash \
    gdb \
    strace \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    x11vnc \
    xvfb \
    fluxbox \
    xterm \
    gcc

# Create a conda environment with Python 3.13
RUN conda create -n myenv python=3.13 -y

# Set the working directory
WORKDIR /app

# Copy the application code and requirements.txt to the container
COPY . /app

# Activate the conda environment and install Python packages
RUN /opt/conda/envs/myenv/bin/pip install --no-cache-dir -r requirements.txt

# Expose the VNC port
EXPOSE 5900

# Start the VNC server and the application
CMD ["sh", "-c", "Xvfb :1 -screen 0 1024x768x16 & x11vnc -display :1 -forever -nopw -create & python main.py"]