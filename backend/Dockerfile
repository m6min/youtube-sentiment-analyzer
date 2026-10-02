FROM python:3.11-slim

WORKDIR /code


COPY ./requirements.txt /code/requirements.txt

RUN pip install --prefer-binary --default-timeout=60 --retries=3 -r /code/requirements.txt


COPY ./app /code/app


COPY ./alembic.ini /code/alembic.ini


COPY ./alembic /code/alembic


COPY ./entrypoint.sh /code/entrypoint.sh


RUN chmod +x /code/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
