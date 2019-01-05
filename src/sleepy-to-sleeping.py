#!/usr/bin/env python3

import sys
import tesladata
from tesladata import log


def sleepy_to_sleep(mongo_db, influx_server="localhost"):
    """
    sleepy_to_sleep calculates the difference in seconds between
    the state 'sleepy' and state 'asleep'. It looks 2 hours back
    in the 'custom_data' collection to find the state 'sleepy' and 
    for every 'sleepy' entry it finds, it will look in the 'vehicle'
    collection if the state change to 'asleep' within 1 hour after the
    'sleepy' state. 

    params:
      mongo_db: a mongodb database handle
      influx_server: the hostname of the influxdb server
    """
    custom_data = tesladata.get_mongo_data(
        mongo_db,
        "custom_data",
        timestamp_start=tesladata.generate_timestamp(min_secs=7200),
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

    config = tesladata.readconfig()
    DEBUG = config["debug"]

    client = tesladata.mongoclient(config["mongo_server"])
    mongo_db = client[config["mongo_database"]]

    sleepy_to_sleep(mongo_db=mongo_db, influx_server=config["influx_server"])


if __name__ == "__main__":
    sys.exit(main())

# End of program
