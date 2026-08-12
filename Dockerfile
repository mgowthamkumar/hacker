FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5501

# Use environment variables for host/port. Default host is localhost to match local-only setups.
# To allow external access from the container (e.g., when deploying), set HOST=0.0.0.0.
CMD ["sh", "-c", "uvicorn backendreal:app --host ${HOST:-127.0.0.1} --port ${PORT:-5501}"]
