FROM python:3-alpine
LABEL maintainer='Richard Arends'

ENV USERNAME='user@example.com'
ENV PASSWORD='secret'
ENV VIN='your vin'
ENV POLL_INTERVAL=60
ENV DEBUG=False
ENV INFLUX_SERVER='influx.example.com'
ENV WRITE_TO_INFLUX=True
ENV MONGO_SERVER='mongo.example.com'
ENV MONGO_DATABASE='tesla'
ENV WRITE_TO_MONGO=True
ENV MQTT_SERVER='mqtt.example.com'
ENV MQTT_USERNAME='mqtt'
ENV MQTT_PASSWORD='secret'
ENV PUBLISH_ON_MQTT=True

RUN apk add --update supervisor && \
  rm -rf /tmp/* /var/cache/apk/* && \
  adduser -D apprunner && \
  mkdir -p /usr/local/tesladata

COPY requirements.txt /usr/local/tesladata/
COPY src/* /usr/local/tesladata/
COPY src/container/config.sh /usr/local/tesladata/
COPY src/container/supervisord.conf /etc/

RUN pip install --no-cache-dir -r /usr/local/tesladata/requirements.txt && \
  chmod 755 /usr/local/tesladata/config.sh && \
  install -o apprunner -g apprunner -m 0640 /dev/null /usr/local/tesladata/config.yaml

WORKDIR /home/apprunner
USER apprunner

RUN mkdir /home/apprunner/cron && \
  echo '*/1 * * * * /usr/local/bin/python3 -u /usr/local/tesladata/mongo-to-influxdb.py' > /home/apprunner/cron/apprunner

CMD [ "/usr/bin/supervisord" ]
