FROM python:3.10-slim

RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git gcc g++ gzip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt -U

COPY . .

RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "./entrypoint.sh" ]
CMD [ "sh", "-c", "if [ \"$DJANGO_DEBUG\" = \"True\" ]; then python3 manage.py runserver 0.0.0.0:8000; else gunicorn backend.wsgi:application --bind 0.0.0.0:8000; fi" ]
