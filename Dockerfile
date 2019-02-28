FROM python:3.6

WORKDIR /workspace/to_redis

RUN pip install -r requirements.txt

COPY ./to_redis/port_to_redis.py /workspace

CMD python /workspace/port_to_redis.py