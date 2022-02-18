FROM python:3.10.2-slim

ENV PYTHONUNBUFFERED=1
RUN pip install -U pip setuptools wheel

COPY . /opt/app
WORKDIR /opt/app

RUN pip install -r requirements.txt && \
    pip install --no-cache-dir -e .

CMD python app/run.py --config && \
    python app/run.py --run --debug
