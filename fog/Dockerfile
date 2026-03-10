FROM python:3.11-slim

WORKDIR /app

COPY fog_node.py /app

# Install necessary Python packages
RUN pip install flask paho-mqtt requests

# Run the fog node
CMD ["python", "fog_node.py"]
