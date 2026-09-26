FROM python:3.11-slim

WORKDIR /code

RUN pip install --no-cache-dir --upgrade pip

COPY ./requirements.txt /code/requirements.txt

RUN pip install -v --default-timeout=60 --no-cache-dir -r /code/requirements.txt


COPY ./app /code/app


COPY ./alembic.ini /code/alembic.ini


COPY ./alembic /code/alembic

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]