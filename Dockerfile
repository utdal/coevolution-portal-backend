FROM python:3.10-slim

RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git gcc

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD [ "gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000" ]
