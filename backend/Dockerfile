FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        gosu \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system nova && adduser --system --ingroup nova nova

COPY pyproject.toml constraints.txt README.md ./
COPY app ./app
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/nova-entrypoint
RUN pip install --no-cache-dir --constraint constraints.txt .

EXPOSE 8000

ENTRYPOINT ["nova-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
