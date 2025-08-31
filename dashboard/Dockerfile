FROM python:3.10-slim

WORKDIR /dashboard

COPY requirements.txt .
COPY ./models /app/models
COPY ./data /app/data

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
