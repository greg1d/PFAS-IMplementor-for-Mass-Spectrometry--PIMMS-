FROM python:3.13
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
ENV NAME PIMMS
CMD ["python", "setup_environment.py"]