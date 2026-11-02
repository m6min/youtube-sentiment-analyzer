FROM python:3.11-slim AS model-builder
WORKDIR /build
ENV HF_HOME=/build/cache
COPY requirements-export.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements-export.txt
COPY tools/export_sentiment.py .
ARG MODEL_REVISION=f6070864c69990a669bf9b8c659a0093062d73e8
RUN --mount=type=cache,target=/build/cache python export_sentiment.py --output /model --work-dir /build/export --revision "$MODEL_REVISION"

FROM python:3.11-slim AS runtime-base

ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false

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

FROM runtime-base AS runtime
COPY --from=model-builder /model /code/app/services/local_model/sentiment
