FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sensor_emulator.py .
CMD ["python", "sensor_emulator.py"]
