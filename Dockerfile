FROM python:3.13

# Install system packages
RUN apt-get update && apt-get install -y python3-tk

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
ENV NAME=PIMMS
CMD ["python", "setup_environment.py"]