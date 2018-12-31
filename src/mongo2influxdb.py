#!/usr/bin/env python3

import time
import json
import yaml
import sys
from time import gmtime, strftime
import tesladata
from tesladata import log


def influx_write(**kwargs):
    if WRITE_TO_INFLUX is True:
        tesladata.influx_write(**kwargs)
    else:
        log("writing to Influx is disabled", level="WARNING")


def vehicle_state(server, data):
    for document in data:
        influx_write(
            servername=server,
            measurement="vehicle_state",
            entity="odometer",
            vin=document["vin"],
            value=document["odometer"],
            ms=document["timestamp"],
        )


def vehicle(server, data):
    for document in data:
        sleeping = 0

        if document["state"] == "asleep":
            sleeping = 1

        influx_write(
            servername=server,
            measurement="vehicle_state",
            entity="sleeping",
            vin=document["vin"],
            value=sleeping,
            ms=document["timestamp"],
        )


def custom_data(server, data):
    for document in data:

        try:
            if document["sleepy"] is True:
                influx_write(
                    servername=server,
                    measurement="custom_data",
                    entity="sleepy",
                    vin=document["vin"],
                    value=1,
                    ms=document["timestamp"],
                )
        except KeyError:
            pass


def charge_state(server, data):
    for document in data:

        influx_write(
            servername=server,
            measurement="charge_state",
            entity="battery_level",
            vin=document["vin"],
            value=document["battery_level"],
            ms=document["timestamp"],
        )

        influx_write(
            servername=server,
            measurement="charge_state",
            entity="ideal_battery_range",
            vin=document["vin"],
            value=float(document["ideal_battery_range"] * 1.609344),
            ms=document["timestamp"],
        )


def sleepy_to_sleep(
    mongo_db, influx_server="localhost"
):
    """
    sleepy_to_sleep calculates the difference in seconds between
    the state 'sleepy' and 'asleep'

    params:
      mongo_db: a mongodb database handle
      influx_server: the hostname of the influxdb server
    """
    custom_data = tesladata.get_mongo_data(
        mongo_db,
        "custom_data",
        timestamp_start=tesladata.generate_timestamp(min_secs=86400),
    )

    for doc in custom_data:
        ts_start = doc["timestamp"]
        ts_end = tesladata.generate_timestamp(timestamp=ts_start, add_secs=3600)

        vehicle_data = tesladata.get_mongo_data(
            mongo_db,
            "vehicle",
            timestamp_start=ts_start,
            timestamp_end=ts_end,
        )

        for vdata in vehicle_data:
            if vdata["state"] == "asleep":
                ts_asleep = vdata["timestamp"]

                influx_write(
                    servername=influx_server,
                    measurement="custom_data",
                    entity="sleepy_to_sleep",
                    vin=vdata["vin"],
                    value=(ts_asleep - ts_start) / 1000,
                    ms=vdata["timestamp"],
                )

                break


def debug(msg):
    if DEBUG is True:
        log(msg, level="DEBUG")


def main():
    """
    Read data from mongo and write (some of) it to InfluxDB
    """
    global DEBUG
    global WRITE_TO_INFLUX

    config = tesladata.readconfig()
    DEBUG = config["debug"]
    WRITE_TO_INFLUX = config["write_to_influx"]

    client = tesladata.mongoclient(config["mongo_server"])
    mongo_db = client[config["mongo_database"]]

    sleepy_to_sleep(
        mongo_db=mongo_db,
        influx_server=config["influx_server"],
    )

    for endpoint in ['charge_state', 'vehicle', 'custom_data', 'vehicle_state']:
        debug("Working on endpoint {}".format(endpoint))

        mongo_posts = tesladata.get_mongo_data(
            mongo_db, endpoint, timestamp_start=tesladata.generate_timestamp(min_secs=300)
        )

        log(
            "Got {} messages from MongoDB for endpoint {}".format(
                len(mongo_posts), endpoint
            )
        )

        try:
            globals()[endpoint](config["influx_server"], mongo_posts)
        except KeyError:
            log("There is no function for {}".format(endpoint), level="ERROR")


if __name__ == "__main__":
    sys.exit(main())

# End of program
