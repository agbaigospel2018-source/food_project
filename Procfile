web: gunicorn belleful_express.wsgi --bind 0.0.0.0:$PORT --workers 2 --threads 4
release: python manage.py tailwind build && python manage.py collectstatic --noinput && python manage.py migrate