FROM python:3.10-slim

WORKDIR /dashboard

COPY dashboard/requirements.txt .
COPY ../models /dashboard/models
COPY ../data /dashboard/data

RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
