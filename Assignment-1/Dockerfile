FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[gcp]"

EXPOSE 8080

CMD ["uvicorn", "diabetes_risk.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
