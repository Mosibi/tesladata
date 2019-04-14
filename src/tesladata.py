import sys
import time
import yaml
import urllib3
import os.path
import json
import datetime
import calendar
#import teslajson
from time import gmtime, strftime
from pymongo import MongoClient
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.request import ProxyHandler, HTTPBasicAuthHandler, HTTPHandler


""" 
The Python classes Connection and Vehicle are imported
from https://github.com/gglockner/teslajson

Small modifications to the Connection class are made to
remove the code that fetched the Tesla API url, api_secret
and api_id from pastebin.com
"""

class Connection(object):
    """Connection to Tesla Motors API"""
    def __init__(self,
            email='',
            password='',
            access_token='',
            proxy_url = '',
            proxy_user = '',
            proxy_password = '',
            baseurl='https://owner-api.teslamotors.com',
            api='/api/1/',
            api_secret='c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220',
            api_id='e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e'
            ):
        
        """Initialize connection object
        
        Sets the vehicles field, a list of Vehicle objects
        associated with your account

        Required parameters:
        email: your login for teslamotors.com
        password: your password for teslamotors.com
        
        Optional parameters:
        access_token: API access token
        proxy_url: URL for proxy server
        proxy_user: username for proxy server
        proxy_password: password for proxy server
        baseurl: Tesla API url
        api_secret: secret token to get access to the Tesla API
        api_id: API id used to get access to the Tesla API
        """
        
        self.proxy_url = proxy_url
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password
        self.baseurl = baseurl
        self.api = api
        
        if access_token:
            self.__sethead(access_token)
        else:
            self.oauth = {
                "grant_type" : "password",
                "client_id" : api_id,
                "client_secret" : api_secret,
                "email" : email,
                "password" : password }
            self.expiration = 0 # force refresh
        self.vehicles = [Vehicle(v, self) for v in self.get('vehicles')['response']]
    
    def get(self, command):
        """Utility command to get data from API"""
        return self.post(command, None)
    
    def post(self, command, data={}):
        """Utility command to post data to API"""
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            auth = self.__open("/oauth/token", data=self.oauth)
            self.__sethead(auth['access_token'],
                           auth['created_at'] + auth['expires_in'] - 86400)
        return self.__open("%s%s" % (self.api, command), headers=self.head, data=data)
    
    def __sethead(self, access_token, expiration=float('inf')):
        """Set HTTP header"""
        self.access_token = access_token
        self.expiration = expiration
        self.head = {"Authorization": "Bearer %s" % access_token}
    
    def __open(self, url, headers={}, data=None, baseurl=""):
        """Raw urlopen command"""
        if not baseurl:
            baseurl = self.baseurl

        _url = '{}{}'.format(baseurl, url)
        req = Request(_url, headers=headers)
    
        try:
            req.data = urlencode(data).encode('utf-8') # Python 3
        except:
            try:
                req.add_data(urlencode(data)) # Python 2
            except:
                pass

        # Proxy support
        if self.proxy_url:
            if self.proxy_user:
                proxy = ProxyHandler({'https': 'https://%s:%s@%s' % (self.proxy_user,
                                                                     self.proxy_password,
                                                                     self.proxy_url)})
                auth = HTTPBasicAuthHandler()
                opener = build_opener(proxy, auth, HTTPHandler)
            else:
                handler = ProxyHandler({'https': self.proxy_url})
                opener = build_opener(handler)
        else:
            opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        return json.loads(resp.read().decode(charset))
        

class Vehicle(dict):
    """Vehicle class, subclassed from dictionary.
    
    There are 3 primary methods: wake_up, data_request and command.
    data_request and command both require a name to specify the data
    or command, respectively. These names can be found in the
    Tesla JSON API."""
    def __init__(self, data, connection):
        """Initialize vehicle class
        
        Called automatically by the Connection class
        """
        super(Vehicle, self).__init__(data)
        self.connection = connection
    
    def data_request(self, name):
        """Get vehicle data"""
        result = self.get('data_request/%s' % name)
        return result['response']
    
    def wake_up(self):
        """Wake the vehicle"""
        return self.post('wake_up')
    
    def command(self, name, data={}):
        """Run the command for the vehicle"""
        return self.post('command/%s' % name, data)
    
    def get(self, command):
        """Utility command to get data from API"""
        return self.connection.get('vehicles/%i/%s' % (self['id'], command))
    
    def post(self, command, data={}):
        """Utility command to post data to API"""
        return self.connection.post('vehicles/%i/%s' % (self['id'], command), data)



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
        output = Connection(username, password)
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
