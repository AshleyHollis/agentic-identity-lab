FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY apps/shared/python/identity_lab_auth /app/identity_lab_auth
COPY apps/shared/python/identity_lab_diagnostics /app/identity_lab_diagnostics
COPY apps/bff/python-fastapi /app/service

WORKDIR /app/service
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir "fastapi>=0.110.0" "uvicorn[standard]>=0.29.0"
ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
