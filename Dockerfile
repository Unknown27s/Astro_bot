FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/chroma_db data/uploads logs

EXPOSE 8000 8501

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
