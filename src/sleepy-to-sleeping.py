#!/usr/bin/env python3

import sys
import tesladata
from tesladata import log


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

    tesladata.sleepy_to_sleep(mongo_db=mongo_db, influx_server=config["influx_server"])


if __name__ == "__main__":
    sys.exit(main())

# End of program
