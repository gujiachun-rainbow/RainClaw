FROM crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/rainclaw-websearch:0.1

WORKDIR /search

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python dependencies (BuildKit cache)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements.txt

# Copy websearch source code
COPY . /search/

EXPOSE 8068

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8068", "--timeout", "120"]
