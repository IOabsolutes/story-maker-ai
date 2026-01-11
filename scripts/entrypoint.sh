#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; do
    sleep 1
done
echo "Database is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin/admin')
else:
    print('Superuser already exists')
"

# Start server
echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
