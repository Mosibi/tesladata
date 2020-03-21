#!/bin/sh

echo "username: ${USERNAME}" > /usr/local/tesladata/config.yaml
echo "password: ${PASSWORD}" >> /usr/local/tesladata/config.yaml
echo "vin: ${VIN}" >> /usr/local/tesladata/config.yaml
echo "poll_interval: ${POLL_INTERVAL}" >> /usr/local/tesladata/config.yaml
echo "debug: ${DEBUG}" >> /usr/local/tesladata/config.yaml
echo "influx_server: ${INFLUX_SERVER}" >> /usr/local/tesladata/config.yaml
echo "write_to_influx: ${WRITE_TO_INFLUX}" >> /usr/local/tesladata/config.yaml
echo "mongo_server: ${MONGO_SERVER}" >> /usr/local/tesladata/config.yaml
echo "mongo_database: ${MONGO_DATABASE}" >> /usr/local/tesladata/config.yaml
echo "write_to_mongo: ${WRITE_TO_MONGO}" >> /usr/local/tesladata/config.yaml
echo "mqtt_server: ${MQTT_SERVER}" >> /usr/local/tesladata/config.yaml
echo "mqtt_username: ${MQTT_USERNAME}" >> /usr/local/tesladata/config.yaml
echo "mqtt_password: ${MQTT_PASSWORD}" >> /usr/local/tesladata/config.yaml
echo "publish_on_mqtt: ${PUBLISH_ON_MQTT}" >> /usr/local/tesladata/config.yaml
