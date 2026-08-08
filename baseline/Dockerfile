FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# /app/data is the dataprep training output, mounted read-only by compose.
# train.py runs once and reuses the artifact while the schema claim matches.
CMD ["sh", "-c", "python train.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
