########################################
# Stage 1 – Build the virtualenv
########################################
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/

# git fetches py-mfdca; gcc/g++ build any sdists. Only needed here.
RUN apt-get update && apt-get install -y --no-install-recommends git gcc g++ \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /usr/src/app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-cache

########################################
# Stage 2 – Runtime image
########################################
FROM python:3.12-slim

RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/src/app
COPY . .

RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "./entrypoint.sh" ]
CMD [ "sh", "-c", "if [ \"$DJANGO_DEBUG\" = \"True\" ]; then python3 manage.py runserver 0.0.0.0:8000; else gunicorn backend.wsgi:application --bind 0.0.0.0:8000; fi" ]
