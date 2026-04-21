FROM crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/python:3.12.13-slim-trixie

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements.txt

COPY app ./app

# Default: run API server (override in compose for worker/beat)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
