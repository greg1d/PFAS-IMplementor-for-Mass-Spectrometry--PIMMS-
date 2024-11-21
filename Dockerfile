FROM continuumio/miniconda3

# Install system packages including debugging tools
RUN apt-get update && apt-get install -y python3-tk bash gdb strace

# Create a conda environment with Python 3.13
RUN conda create -n myenv python=3.13 -y

# Activate the conda environment
SHELL ["conda", "run", "-n", "myenv", "/bin/sh", "-c"]

WORKDIR /app
COPY . /app

# Install Python packages using pip within the conda environment
RUN conda run -n myenv pip install --no-cache-dir -r requirements.txt

EXPOSE 80
ENV NAME=PIMMS

# Use conda run to execute the command within the conda environment
CMD ["conda", "run", "-n", "myenv", "/bin/sh", "-c", "python --version && python setup_environment.py && tail -f /dev/null"]