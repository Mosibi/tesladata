#!/usr/bin/env python3

# Read data from the Tesla API and store it in MongoDB
#
# Richard Arends (21-12-2028)

import sys
import time
import os.path
import yaml
from pymongo import MongoClient
import teslajson


def debug_msg(message):
    if DEBUG is True:
        print(
            "{0} DEBUG: {1}".format(
                time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
            )
        )


def error_msg(message):
    print(
        "{0} ERROR: {1}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
        )
    )


def warning_msg(message):
    print(
        "{0} WARNING: {1}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
        )
    )


def info_msg(message):
    print(
        "{0} INFO: {1}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
        )
    )


def read_config(configfile):
    try:
        with open(configfile, "r") as ymlfile:
            cfg = yaml.load(ymlfile)
    except Exception as err:
        error_msg("could not open/read config file {}: {}".format(configfile, err))

    return cfg


def get_all_cardata(vehicle):
    endpoints = {
        "charge_state",
        "climate_state",
        "drive_state",
        "gui_settings",
        "vehicle_state",
        "vehicle_config",
    }
    data = {}

    for endpoint in endpoints:
        try:
            endpoint_data = vehicle.data_request(endpoint)
            endpoint_data["vin"] = vehicle["vin"]

            data.update({endpoint: endpoint_data})

            debug_msg("get_all_cardata: {}, data: {}".format(endpoint, data))

        except Exception as err:
            warning_msg(
                "Could not get data from Tesla with vin {}: {}".format(
                    vehicle["vin"], str(err)
                )
            )

    return data


def mongo_write(db, collection_name, json_data):
    if WRITE_TO_MONGO is True:
        # Create a collection handle
        collection = db[collection_name]

        try:
            result = collection.insert_one(json_data)
            debug_msg("Inserted a document into mongo: {}".format(result.inserted_id))
        except Exception as err:
            error_msg("An error occured while writing data to Mongo, {}".format(err))
            error_msg("The following was not written to mongo: {}".format(json_data))
            sys.exit(1)


def iterate_data(data):
    for i in data:
        print("{}: {}".format(i, data[i]))


def sleepy(drive_state):
    if drive_state["shift_state"] is None:
        return True
    else:
        return False


def connect_to_tesla_api(username, password):
    output = None

    try:
        output = teslajson.Connection(username, password)
    except Exception as err:
        warning_msg("Could not connect to the Tesla API: {}".format(str(err)))

    return output


def get_vehicle(username, password, vin):
    vehicle = None
    connection = connect_to_tesla_api(username, password)

    try:
        for v in connection.vehicles:
            if v["vin"] == vin:
                vehicle = v
    except AttributeError:
        # If getting data failed, a AttributeError is raised when
        # we try to itterate over 'connection.vehicles' Just pass here
        # and let the next code handle this situation
        pass

    if vehicle is None:
        error_msg("Could not get/find vehicle information from the Tesla API")
        sys.exit(99)
    else:
        if DEBUG is True:
            print("vehicle: {}".format(dict(vehicle)))

        return vehicle


def poller(vehicle, last_time_sleepy, mongo_db):
    if last_time_sleepy > 0:
        # The car want's to sleep, so exit the while loop.
        # But if the car is allready sleepy for 30 minutes, set
        # last_time_sleepy to 0 and start polling it again.

        seconds_sleepy = int(time.time()) - last_time_sleepy

        if seconds_sleepy < 3600:
            minutes = int(seconds_sleepy / 60)
            info_msg(
                "Tesla with vin {} is sleepy, but still online for {} minutes".format(
                    vehicle["vin"], minutes
                )
            )
            return last_time_sleepy
        else:
            info_msg(
                "Tesla with vin {} is 60 minutes sleepy, we start polling it again".format(
                    vehicle["vin"]
                )
            )
            last_time_sleepy = 0
    else:
        try:
            car_data = get_all_cardata(vehicle)
            charge_state = car_data["charge_state"]

            # Write data for every endpoint polled from the Tesla to Mongo
            for endpoint in car_data:
                mongo_write(mongo_db, endpoint, car_data[endpoint])

            """
            Detect if the car want's to go to sleep. If the car is charging we keep polling it,
            preventing it to go to sleep.
            """
            if (
                sleepy(car_data["drive_state"]) is True
                and charge_state["charging_state"] != "Charging"
            ):
                info_msg("Tesla with vin {} is sleepy".format(vehicle["vin"]))
                data = {
                    "timestamp": int(round(time.time() * 1000)),
                    "sleepy": True,
                    "vin": vehicle["vin"],
                }
                mongo_write(mongo_db, "custom_data", data)
                last_time_sleepy = int(time.time())

                # wait 20 minutes before doing anything else
                time.sleep(1200)
        except KeyError as endpoint_name:
            error_msg(
                "No data received from Tesla with vin {} for endpoint {}".format(
                    vehicle["vin"], endpoint_name
                )
            )

    return last_time_sleepy


def main():
    global DEBUG
    global WRITE_TO_MONGO

    last_time_sleepy = 0

    # Get the config file
    configfile = None
    for filename in [
        "/usr/local/tesladata/config.yaml",
        "./src/config.yaml",
        "./config.yaml",
    ]:
        if os.path.isfile(filename):
            configfile = filename

    if configfile is None:
        error_msg("Could not find a configuration file for Tesladata")
        sys.exit(99)

    config = read_config(configfile)
    DEBUG = config["debug"]
    WRITE_TO_MONGO = config["write_to_mongo"]

    if WRITE_TO_MONGO is True:
        client = MongoClient("mongodb://{}:27017/".format(config["mongo_server"]))
        mongo_db = client[config["mongo_database"]]

    while True:
        # On every loop, fetch fresh vehicle information from the Tesla API.
        vehicle = get_vehicle(config["username"], config["password"], config["vin"])
        vehicle["timestamp"] = int(round(time.time() * 1000))

        # Write 'vehicle' information in Mongo
        mongo_write(mongo_db, "vehicle", dict(vehicle))

        if vehicle["state"] == "online":
            last_time_sleepy = poller(vehicle, last_time_sleepy, mongo_db)
        elif vehicle["state"] == "offline":
            info_msg("Tesla with vin {} is offline".format(vehicle["vin"]))
            last_time_sleepy = 0
        elif vehicle["state"] == "asleep":
            info_msg("Tesla with vin {} is sleeping".format(vehicle["vin"]))
            last_time_sleepy = 0
        elif vehicle["state"] == "waking":
            info_msg("Tesla with vin {} is waking up".format(vehicle["vin"]))
            last_time_sleepy = 0
        else:
            warning_msg(
                "Tesla with vin {} has state {}. This state is unknown to us".format(
                    vehicle["vin"], vehicle["state"]
                )
            )
            last_time_sleepy = 0

        time.sleep(config["poll_interval"])


if __name__ == "__main__":
    sys.exit(main())

# End of program
