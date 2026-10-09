FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git gcc g++ gzip

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY . .

RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "./entrypoint.sh" ]
CMD [ "sh", "-c", "if [ \"$DJANGO_DEBUG\" = \"True\" ]; then python3 manage.py runserver 0.0.0.0:8000; else gunicorn backend.wsgi:application --bind 0.0.0.0:8000; fi" ]
