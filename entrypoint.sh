#!/bin/sh
set -e

# 1. Coletar estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# 2. Rodar Migrations (Apenas o migrate)
echo "Aplicando as migrações do banco de dados..."
python manage.py migrate --noinput

# 3. Execução
echo "Iniciando Gunicorn..."
exec "$@"