FROM crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/rainclaw-sandbox:0.2
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt 


RUN mkdir -p /home/rainclaw && chmod -R 777 /home/rainclaw

# ── 3. 项目文件 ────────────────────────────────────────────────────────
COPY ./seekr_sdk.py /opt/python3.12/lib/python3.12/site-packages/seekr_sdk.py
COPY tool_runner.py /app/_tool_runner.py
