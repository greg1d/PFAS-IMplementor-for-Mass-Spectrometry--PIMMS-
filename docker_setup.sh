# docker_setup.ps1

$IMAGE_NAME = "gregkudzin/my-python-app"
$CONTAINER_NAME = "PIMMS"

# Log in to Docker Hub
Write-Output "Logging in to Docker Hub..."
docker login

# Pull the Docker image from Docker Hub
Write-Output "Pulling Docker image from Docker Hub..."
docker pull $IMAGE_NAME

# Stop and remove any existing container with the same name
Write-Output "Stopping and removing any existing container with the name $CONTAINER_NAME..."
docker stop $CONTAINER_NAME -ErrorAction SilentlyContinue
docker rm $CONTAINER_NAME -ErrorAction SilentlyContinue

# Run the Docker container
Write-Output "Running the Docker container..."
docker run -d --name $CONTAINER_NAME $IMAGE_NAME

# Verify the container is running
Write-Output "Verifying the container is running..."
docker ps

# Access the running container (optional)
# Uncomment the following line if you want to access the container immediately after running it
# docker exec -it $CONTAINER_NAME /bin/sh

Write-Output "Docker setup complete."