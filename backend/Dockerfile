FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system nova && adduser --system --ingroup nova nova
RUN mkdir -p /data /intake && chown -R nova:nova /data /intake

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

USER nova
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

