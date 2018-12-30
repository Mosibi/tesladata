#!/usr/bin/env python3

# Read data from the Tesla API and store it in MongoDB
#
# Richard Arends (21-12-2028)

import sys
import time
import tesladata
from tesladata import log


def debug(msg):
    if DEBUG is True:
        log(msg, level="DEBUG")


def mongo_write(db=None, collection_name=None, json_data=None):
    if WRITE_TO_MONGO is True:
        tesladata.mongo_write(
            db=db, collection_name=collection_name, json_data=json_data
        )
    else:
        log("Writing to MongoDB is disabled")


def iterate_data(data):
    for i in data:
        print("{}: {}".format(i, data[i]))


def sleepy(drive_state):
    if drive_state["shift_state"] is None:
        return True
    else:
        return False


def poller(vehicle, last_time_sleepy, mongo_db):
    if last_time_sleepy > 0:
        # The car want's to sleep, so exit the while loop.
        # But if the car is allready sleepy for 30 minutes, set
        # last_time_sleepy to 0 and start polling it again.

        seconds_sleepy = int(time.time()) - last_time_sleepy

        if seconds_sleepy < 3600:
            minutes = int(seconds_sleepy / 60)
            log(
                "Tesla with vin {} is sleepy, but still online for {} minutes".format(
                    vehicle["vin"], minutes
                )
            )
            return last_time_sleepy
        else:
            log(
                "Tesla with vin {} is 60 minutes sleepy, we start polling it again".format(
                    vehicle["vin"]
                )
            )
            last_time_sleepy = 0
    else:
        try:
            car_data = tesladata.get_all_cardata(vehicle)
            charge_state = car_data["charge_state"]

            # Write data for every endpoint polled from the Tesla to Mongo
            for endpoint in car_data:
                mongo_write(
                    db=mongo_db, collection_name=endpoint, json_data=car_data[endpoint]
                )

            """
            Detect if the car want's to go to sleep. If the car is charging we keep polling it,
            preventing it to go to sleep.
            """
            if (
                sleepy(car_data["drive_state"]) is True
                and charge_state["charging_state"] != "Charging"
            ):
                log("Tesla with vin {} is sleepy".format(vehicle["vin"]))

                data = {
                    "timestamp": int(round(time.time() * 1000)),
                    "sleepy": True,
                    "vin": vehicle["vin"],
                }

                mongo_write(db=mongo_db, collection_name="custom_data", json_data=data)
                last_time_sleepy = int(time.time())

                # wait 20 minutes before doing anything else
                time.sleep(1200)
        except KeyError as endpoint_name:
            log(
                "No data received from Tesla with vin {} for endpoint {}".format(
                    vehicle["vin"], endpoint_name
                ),
                level="ERROR",
            )

    return last_time_sleepy


def main():
    global DEBUG
    global WRITE_TO_MONGO

    config = tesladata.readconfig()
    DEBUG = config["debug"]
    WRITE_TO_MONGO = config["write_to_mongo"]

    last_time_sleepy = 0

    if WRITE_TO_MONGO is True:
        client = tesladata.mongoclient(config["mongo_server"])
        mongo_db = client[config["mongo_database"]]
    else:
        mongo_db = None

    while True:
        try:
            # On every loop, fetch fresh vehicle information from the Tesla API.
            vehicle = tesladata.get_vehicle(
                config["username"], config["password"], config["vin"]
            )
            vehicle["timestamp"] = int(round(time.time() * 1000))

            # Write 'vehicle' information in Mongo
            mongo_write(db=mongo_db, collection_name="vehicle", json_data=dict(vehicle))

            if vehicle["state"] == "online":
                last_time_sleepy = poller(vehicle, last_time_sleepy, mongo_db)
            elif vehicle["state"] == "offline":
                log("Tesla with vin {} is offline".format(vehicle["vin"]))
                last_time_sleepy = 0
            elif vehicle["state"] == "asleep":
                log("Tesla with vin {} is sleeping".format(vehicle["vin"]))
                last_time_sleepy = 0
            elif vehicle["state"] == "waking":
                log("Tesla with vin {} is waking up".format(vehicle["vin"]))
                last_time_sleepy = 0
            else:
                log(
                    "Tesla with vin {} has state {}. This state is unknown to us".format(
                        vehicle["vin"], vehicle["state"]
                    ),
                    level="WARNING",
                )
                last_time_sleepy = 0
        except KeyError:
            # This can happen when we did not receive data from the Tesla API.
            # Just accept it and try it the next time
            pass

        time.sleep(config["poll_interval"])


if __name__ == "__main__":
    sys.exit(main())

# End of program
