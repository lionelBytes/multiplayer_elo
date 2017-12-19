FROM python:2-alpine

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt
RUN python -m unittest discover

EXPOSE 8000

CMD gunicorn -b 0.0.0.0:8000 "app:create()"
