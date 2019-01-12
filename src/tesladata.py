import sys
import time
import yaml
import urllib3
import os.path
import teslajson
from time import gmtime, strftime
from pymongo import MongoClient


def log(message, level="INFO"):
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]

    if level not in levels:
        raise ValueError("Level {} is not supported by the log function".format(level))

    print(
        "{0} {1}: {2}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), level, message
        )
    )


def readconfig(**kwargs):
    configfile = kwargs.get("configfile", None)

    if configfile is None:
        # Try to find the config file in
        # common paths
        for filename in [
            "/usr/local/tesladata/config.yaml",
            "./src/config.yaml",
            "./config.yaml",
        ]:
            if os.path.isfile(filename):
                configfile = filename

    if configfile is None:
        raise ValueError("Could not find a configuration file for Tesladata")

    with open(configfile, "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    return cfg


def debug_document(document):
    e = int(document["timestamp"] / 1000)
    t = time.localtime(e)

    log(
        "document: {} {}".format(strftime("%a, %d %b %Y %H:%M:%S +0000", t), document),
        level="DEBUG",
    )


def ms_to_date(ms):
    e = int(ms / 1000)
    t = time.localtime(e)
    return strftime("%a, %d %b %Y %H:%M:%S +0000", t)


def generate_timestamp(timestamp=(time.time() * 1000), add_secs=None, min_secs=None):
    # Return the timestamp in milliseconds, adding or substracting the seconds
    # given as an argument. If timestamp is empty, the current time is used

    if add_secs is None and min_secs is None:
        raise ("Argument add_secs or min_secs must be present")

    if add_secs is not None and min_secs is not None:
        raise ("Choose between add_secs or mins_secs, both is not possible")

    if add_secs is not None:
        mill = add_secs * 1000
        return int(round(timestamp)) + mill

    if min_secs is not None:
        mill = min_secs * 1000
        return int(round(timestamp)) - mill


def get_mongo_data(
    db_handle, collection_name, timestamp_start=None, timestamp_end=None
):
    """
    get_mongo_data params:
    db_handle: a mongodb database handle
    collection_name: a mongodb collection
    timestamp_start and timestamp_end: timestamp in seconds (epoch)
    """
    data = []

    if timestamp_start is None:
        # By default look 5 minutes back
        timestamp_start = generate_timestamp(min_secs=300)

    if timestamp_end is None:
        # Use the current time
        timestamp_end = int(round(time.time() * 1000))

    if timestamp_start > timestamp_end:
        raise ValueError("start timestamp must be smaller then end timestamp")

    collection = db_handle[collection_name]

    try:
        documents = collection.find(
            {
                "$and": [
                    {"timestamp": {"$gte": timestamp_start}},
                    {"timestamp": {"$lte": timestamp_end}},
                ]
            }
        )

        for document in documents:
            data.append(document)

        return data
    except Exception as err:
        log("An exception in function get_mongo_data: {}".format(err), level="ERROR")


def influx_write(**kwargs):
    # Arguments that must be passed
    try:
        servername = str(kwargs["servername"])
        measurement = str(kwargs["measurement"])
        entity = str(kwargs["entity"])
        vin = str(kwargs["vin"])
        value = kwargs["value"]
    except KeyError as argument:
        print("missing argument {} for function influx_write".format(argument))

    # Arguments that have a default value that can be overriden
    serverport = int(kwargs.get("serverport", 8086))
    database = str(kwargs.get("database", "tesla"))
    ms = int(kwargs.get("ms", int(time.time() * 1000)))

    try:
        binary_data = "{0},entity={1},vin={2} value={3} {4}".format(
            measurement, entity, vin, value, ms
        )
        url = "http://{}:{}/write?db={}&precision=ms".format(
            servername, serverport, database
        )

        # Do the HTTP request to post the data
        http = urllib3.PoolManager()
        r = http.request("POST", url, body=binary_data)

        if r.status != 204:
            log(
                "An error occured while writing data to influx, HTTP code {}".format(
                    r.status
                ),
                level="ERROR",
            )
    except ValueError as err:
        log(
            "An error occured while writing data to influx: {}".format(err),
            level="ERROR",
        )
    except urllib3.exceptions.MaxRetryError:
        log(
            "Could not connect to influx server {}. Maximum connection retries exceeded".format(
                servername
            ),
            level="ERROR",
        )
    except urllib3.exceptions.NewConnectionError as new_conn_err:
        log(
            "Could not connect to influx server {}: {}".format(
                servername, new_conn_err
            ),
            level="ERROR",
        )
    except ConnectionRefusedError:
        log(
            "Could not connect to influx server {}. Connection refused".format(
                servername
            ),
            level="ERROR",
        )


def mongo_write(db=None, collection_name=None, json_data=None):
    # Create a collection handle
    collection = db[collection_name]

    try:
        result = collection.insert_one(json_data)
    except Exception as err:
        log(
            "An error occured while writing data to Mongo, {}".format(err),
            level="ERROR",
        )
        log(
            "The following was not written to mongo: {}".format(json_data),
            level="ERROR",
        )


def connect_to_tesla_api(username, password):
    output = None

    try:
        output = teslajson.Connection(username, password)
    except Exception as err:
        log("Could not connect to the Tesla API: {}".format(str(err)), level="WARNING")

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
        log("Could not get/find vehicle information from the Tesla API", level="ERROR")

    return vehicle


def mongoclient(server):
    return MongoClient("mongodb://{}:27017/".format(server))


def get_all_cardata(vehicle):
    del_from_data = []

    try:
        data = vehicle.get("data")["response"]

        for entry in data:
            # The 'data' command returns a python dict the 'vehicle'
            # endpoint data in the root of the dict and the endpoints
            # within the endpoint name, thus
            #
            # response:
            #   id:
            #   display_name:
            #   charge_state:
            #     battery_level:
            #   drive_state:
            #     shift_state:
            #
            # In the above example we only want to keep 'charge_state'
            # and 'drive_state' since that's the endpoint data we want to
            # return.
            if type(data[entry]) is dict:
                data[entry]["vin"] = vehicle[
                    "vin"
                ]  # Add 'vin' if it is missing in an endpoint data stream
            else:
                # We only want to return endpoint data, other data
                # is not of type(dict), so we remove it from the 'data' dict
                del_from_data.append(entry)

        for item in del_from_data:
            # The actual remove from dict is done here, python
            # does not like it when you remove something from a
            # dict while you are looping over that dict
            del data[item]

        return data
    except Exception as err:
        log(
            "Could not get data from Tesla with vin {}: {}".format(
                vehicle["vin"], str(err)
            ),
            level="WARNING",
        )


def get_endpoint(vehicle, endpoint):
    data = {}

    try:
        endpoint_data = vehicle.data_request(endpoint)
        endpoint_data["vin"] = vehicle["vin"]

        data.update({endpoint: endpoint_data})

    except Exception as err:
        log(
            "Could not get data from Tesla with vin {}: {}".format(
                vehicle["vin"], str(err)
            ),
            level="WARNING",
        )

    return data


def get_est_ideal_maxrange(charge_state):
    """
    Calculate the maxrange based on the current charge level
    and ideal_battery_range
    """
    est_ideal_maxrange = 0

    try:
        ideal_battery_range = charge_state["ideal_battery_range"] * 1.609344
        est_ideal_maxrange = (ideal_battery_range / charge_state["battery_level"]) * 100
    except KeyError:
        log("missing charge_data value, cannot compute maxrange", level="ERROR")

    output = {
        "timestamp": charge_state["timestamp"],
        "est_ideal_maxrange": est_ideal_maxrange,
        "vin": charge_state["vin"],
    }

    return output


def sleepy_to_sleep(mongo_db, influx_server="localhost", secondsback=7200):
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
    custom_data = get_mongo_data(
        mongo_db,
        "custom_data",
        timestamp_start=generate_timestamp(min_secs=secondsback),
    )

    for doc in custom_data:
        ts_start = doc["timestamp"]
        ts_end = generate_timestamp(timestamp=ts_start, add_secs=3600)

        vehicle_data = get_mongo_data(
            mongo_db, "vehicle", timestamp_start=ts_start, timestamp_end=ts_end
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
