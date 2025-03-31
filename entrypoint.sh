#!/bin/bash

# Ожидаем, пока база данных будет доступна
echo "Waiting for PostgreSQL to start..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started."

# Выполняем миграции базы данных
echo "Initializing database..."
python -c "from app.database.DatabaseInitializer import init_db; init_db()"
echo "Database initialized."

# Запускаем приложение
exec "$@"