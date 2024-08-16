FROM python:3.10-slim

RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git gcc g++

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate
EXPOSE 8000
CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]
