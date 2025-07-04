# ---- Base Image ----
FROM python:3.11-slim

# ---- Set Workdir ----
WORKDIR /app

# ---- Install System Dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---- Install Python Dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Project Files ----
COPY . .

# ---- Set Env Variables ----
ENV PYTHONUNBUFFERED=1 \
    TOKENIZERS_PARALLELISM=false

EXPOSE 8000

# ---- Health Check ----
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# ---- Run Application ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]