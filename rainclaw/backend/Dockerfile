ARG BASE_IMAGE=crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/python:3.12.13-slim-trixie
FROM ${BASE_IMAGE}

ARG USE_MIRROR=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      libxrender1 \
      libxext6 \
      libx11-6

# Install all Python dependencies (BuildKit cache)
COPY ./requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements.txt 

# Install seekr_sdk (single-file client for websearch microservice)
COPY ./seekr_sdk.py /usr/local/lib/python3.12/site-packages/seekr_sdk.py

# Copy backend code
COPY . /app/backend

# Copy built-in skills into image (not mounted from host, avoids macOS case-insensitivity issues)
COPY ./builtin_skills /app/builtin_skills

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
