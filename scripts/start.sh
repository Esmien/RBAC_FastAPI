#!/bin/bash

set -e

# Накатываем миграции до актуальной версии
echo "Применяю миграции..."
alembic upgrade head

# Запускаем сервер
echo "Запуск сервера..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload