FROM python:2

RUN apt-get update

RUN apt-get install -y mysql-client

ADD . /tmp/app

RUN cd /tmp/app && python setup.py install

RUN pip install gunicorn gevent

EXPOSE 10000

CMD gunicorn -w 8 -b 0.0.0.0:10004 -k gevent tomato.api.wsgi:app
