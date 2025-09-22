FROM python:3.11-slim

WORKDIR /server

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .

CMD ["uvicorn", "api_products.main:app", "--host", "0.0.0.0", "--port", "8000"]
