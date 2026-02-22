FROM python:3.12-slim

WORKDIR /srv/repomesh-api

COPY apps/api/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./alembic.ini

EXPOSE 8787
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8787"]
