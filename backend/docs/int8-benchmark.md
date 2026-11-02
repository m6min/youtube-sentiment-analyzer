# INT8 deployment check

Date: 2026-11-02

Model: `savasy/bert-base-turkish-sentiment-cased`

Source revision: `f6070864c69990a669bf9b8c659a0093062d73e8`

The exported INT8 artifact is 106.6 MiB. Runtime uses ONNX Runtime 1.31.1,
Tokenizers 0.22.2, one inference thread, batch size 1, and a 128-token limit.
The model does not require PyTorch or an inference API in the running service.

## Docker memory test

Tested with Docker Desktop Linux, `--memory=512m --memory-swap=512m`, and
`--network=none`. Both the title model and sentiment model were loaded through
the application's FastAPI lifespan. The final `yt-analyzer:int8` image was built successfully from the Dockerfile,
including automatic model download, FP32 export, and INT8 quantization on Linux.
The test used the model bundled inside that image; no external model mount was
used. No CPU quota was imposed.

| Workload | Inference time | Container memory peak so far |
| --- | ---: | ---: |
| 30 short comments | 0.59 s | 362.8 MiB |
| 100 short comments | 1.98 s | 362.8 MiB |
| 500 short comments | 10.31 s | 363.5 MiB |
| Two simultaneous requests, each with 30 long comments | — | 444.8 MiB |
| HTTP `/analyze`, 40 comments, followed by `/health` | HTTP 200 | 444.8 MiB |

The process completed successfully without swap or an out-of-memory kill.
Container memory is read from cgroup v2 `memory.peak`; process peak RSS is also
printed by the script and can differ because shared/file-backed memory is
accounted differently. The HTTP test uses real routes and real models, with
YouTube calls and database access mocked. This does not validate production
credentials, database connectivity, migrations, or Render CPU latency.

## Conversion smoke comparison

The original FP32 ONNX model and the INT8 model agreed on 19 of 20 included
examples. The changed example was `Yeni bölüm ne zaman gelecek?`. This is a
small regression check for quantization drift, not a sentiment accuracy score.

## Reproduction

See the commands in the root README and the scripts in `backend/tools`.
`pytest` also passes all five tests inside the final Linux image (1.53 s): the two original API tests and three
sentiment tests covering batching, label mapping, empty input, and invalid output.
