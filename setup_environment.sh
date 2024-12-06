#!/bin/bash

# Define variables
IMAGE_NAME="gregkudzin/my-python-app"
CONTAINER_NAME="PIMMS"

# Build the Docker image
docker build . -t $IMAGE_NAME

# Get the current directory
CURRENT_DIR=$(pwd)

# Run the Docker container
docker run -it --rm \
    --name $CONTAINER_NAME \
    -p 8787:8787 \
    -e DISPLAY=$DISPLAY \
    -v "$CURRENT_DIR":/home/work \
    --workdir /home/work \
    $IMAGE_NAME