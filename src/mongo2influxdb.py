#!/usr/bin/env python3

import time
import json
import yaml
import sys
import argparse
from time import gmtime, strftime
import endpoints
import tesladata
from tesladata import log


def sleepy_to_sleep(mongo_db, influx_server="localhost"):
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
            mongo_db, "vehicle", timestamp_start=ts_start, timestamp_end=ts_end
        )

        for vdata in vehicle_data:
            if vdata["state"] == "asleep":
                ts_asleep = vdata["timestamp"]

                tesladata.influx_write(
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

    parser = argparse.ArgumentParser(
        description="Read data from mongo and write (some of) it to InfluxDB"
    )
    parser.add_argument(
        "--configfile",
        help="path to config.yaml",
        required=False,
        default="/usr/local/tesladata/config.yaml",
    )
    parser.add_argument(
        "--secondsback",
        default=3600,
        help="fetch documents from mongo that are this seconds old and newer. default is 3600 (1 hour)",
        required=False,
    )
    args = parser.parse_args()

    configfile = str(args.configfile)
    secondsback = int(args.secondsback)

    config = tesladata.readconfig(configfile)
    DEBUG = config["debug"]

    client = tesladata.mongoclient(config["mongo_server"])
    mongo_db = client[config["mongo_database"]]

    sleepy_to_sleep(mongo_db=mongo_db, influx_server=config["influx_server"])

    for collection in ["charge_state", "vehicle", "custom_data", "vehicle_state"]:
        debug("Working on collection {}".format(collection))

        mongo_documents = tesladata.get_mongo_data(
            mongo_db,
            collection,
            timestamp_start=tesladata.generate_timestamp(min_secs=300),
        )

        log(
            "Got {} messages from MongoDB for collection {}".format(
                len(mongo_documents), collection
            )
        )

        try:
            method_to_call = getattr(endpoints, collection)

            for doc in mongo_documents:
                method_to_call(config["influx_server"], doc)
        except KeyError:
            log("There is no function for {}".format(collection), level="ERROR")


if __name__ == "__main__":
    sys.exit(main())

# End of program
