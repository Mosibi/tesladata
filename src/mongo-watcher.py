#!/usr/bin/env python3

import time
import json
import sys
import paho.mqtt.client as mqtt
import tesladata
import endpoints
from tesladata import log


def debug(msg):
    if DEBUG is True:
        log(msg, level="DEBUG")


def publish_message(mqtt_client, msg, mqtt_path):
    mqtt_client.publish(mqtt_path, payload=msg, qos=0, retain=True)
    debug(
        "published message {0} on topic {1} at {2}".format(
            msg, mqtt_path, time.asctime(time.localtime(time.time()))
        )
    )


def recon(mqtt_client):
    try:
        mqtt_client.reconnect()
        log("Successfull reconnected to the MQTT server")
    except:
        log(
            "Could not reconnect to the MQTT server. Trying again in 10 seconds",
            level="WARNING",
        )
        time.sleep(10)
        recon(mqtt_client)


def on_connect(mqtt_client, userdata, flags, rc):
    log("Successfull reconnected to the MQTT server")


def on_disconnect(mqtt_client, userdata, rc):
    if rc != 0:
        log("Unexpected disconnection from MQTT, trying to reconnect", level="WARNING")
        recon(mqtt_client)


def main():
    """
    Watch the 'tesla' database for changes. If a document has changed,
    call the 'write to influx' endpoint and publish the message on MQTT
    """

    global DEBUG

    config = tesladata.readconfig()
    DEBUG = config["debug"]

    mongo_client = tesladata.mongoclient(config["mongo_server"])
    tesladb = mongo_client[config["mongo_database"]]

    mqtt_client = mqtt.Client("tesladata")
    mqtt_client.username_pw_set(
        username=config["mqtt_username"], password=config["mqtt_password"]
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.connect(config["mqtt_server"], port=1883, keepalive=45)

    try:
        for document in tesladb.watch([{"$match": {"operationType": "insert"}}]):
            data = document["fullDocument"]
            collection = document["ns"]["coll"]
            del data["_id"]

            if config["publish_on_mqtt"] is True:
                json_full_document = json.dumps(data)
                publish_message(
                    mqtt_client=mqtt_client,
                    msg=json_full_document,
                    mqtt_path="{}/{}".format("tesla", collection),
                )

            if config["write_to_influx"] is True:
                method_to_call = getattr(endpoints, collection)

                try:
                    method_to_call(config["influx_server"], data)
                except AttributeError as attributeerr:
                    log(
                        "there is no function for {} in module endpoints".format(
                            attributeerr
                        )
                    )
    except Exception as err:
        log("error: {}".format(err), level="ERROR")


if __name__ == "__main__":
    sys.exit(main())

# End of program
