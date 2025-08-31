FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
COPY ../models /app/models
COPY ../data /app/data

RUN pip install --no-cache-dir -r requirements.txt

# Copy app and simulator
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default: start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
