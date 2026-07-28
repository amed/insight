FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# the model is trained from the pilot data at container start, so it can never go stale
CMD ["sh", "-c", "python train.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
