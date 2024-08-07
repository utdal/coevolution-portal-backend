# coevolution-portal-backend

This backend uses Django to host the API. Celery is used to manage tasks and Redis is used by Celery.

**To run:**
* `docker compose up`

Then go to `localhost:8000/api/`

You might want to add yourself as an admin:
`python manage.py createsuperuser --username admin`
