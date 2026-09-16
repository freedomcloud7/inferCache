FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install compatible setuptools first (fixes the legacy backend error)
RUN pip install --no-cache-dir "setuptools>=68" wheel

# Install Python dependencies from requirements.txt (non-editable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
