web: gunicorn belleful_express.wsgi --bind 0.0.0.0:$PORT  
release: python manage.py collectstatic --noinput && python manage.py migrate
release: python manage.py tailwind build