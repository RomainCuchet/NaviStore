FROM python:3.11-slim

WORKDIR /server

COPY server_requirements.txt .
RUN pip install --no-cache-dir -r server_requirements.txt

COPY server/ .

CMD ["uvicorn", "api_navimall.main:app", "--host", "0.0.0.0", "--port", "8000"]
