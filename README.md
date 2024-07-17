# coevolution-portal-backend

The backend uses Django to host the API. Celery is used to manage tasks and Redis is used by Celery.

To run:
* Install Django, Celery, and Redis: pip install -r requirements.txt
* Start Redis: docker run -p 6379:6379 redis (if using Docker)
* Start a Celery worker: celery -A backend worker --loglevel=info
* Start Django: python manage.py runserver

A basic demo is at localhost:8000/api/demo/

api/tasks.py contains the (dummy) tasks
