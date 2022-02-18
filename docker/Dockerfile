FROM python:3.10.2-slim

ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get -y install gcc
RUN pip install -U pip setuptools wheel

COPY . /opt/app
WORKDIR /opt/app

RUN pip install -r requirements.txt && \
    pip install --no-cache-dir -e .

CMD python app/bootstrap.py && \
    python app/run.py --run --debug
