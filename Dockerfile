# Backend image — serves both the API (`api`) and the voice agent (`agent`).
FROM python:3.12-slim

# libgomp1 is required by onnxruntime (Silero VAD used by the agent).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# SQLite databases live here; mount a volume to persist across restarts.
RUN mkdir -p /app/data

EXPOSE 8000

# Override in docker-compose per service (api vs agent).
CMD ["python", "-m", "proximus", "api"]
