# Stage 1: build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/src ./src
COPY frontend/public ./public
RUN npm run build

# Stage 2: Python backend + React build
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY app_checkMoney.py .
COPY app_checkLog.py .
COPY app_transaction.py .
COPY app_checkChain.py .
COPY ledger/ ./ledger/

COPY --from=frontend-builder /frontend/build ./frontend/build

ENV LEDGER_PATH=/storage
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python", "app.py"]
