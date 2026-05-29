FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpq-dev \
    gcc \
    python3-dev \
    && pip install --no-cache-dir "psycopg[c]" \
    && apt-get purge -y --auto-remove gcc python3-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --home /app appuser
# 4. Copia o código já definindo o dono (evita problemas de permissão)
COPY --chown=appuser:appuser . .

# 5. Garante execução do entrypoint
RUN chmod +x /app/entrypoint.sh

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]

# Ajuste sugerido para 4 workers (Assumindo uma VPS com pelo menos 2 núcleos)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "core.wsgi:application"]