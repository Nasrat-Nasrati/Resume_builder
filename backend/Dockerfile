FROM python:3.12.7-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install --timeout 180 --retries 8 -r requirements.txt
RUN python -m playwright install --with-deps chromium
COPY . .
RUN python manage.py check
EXPOSE 8000
