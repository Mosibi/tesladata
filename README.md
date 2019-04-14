# Tesladata
This toolset polls data from the Tesla API and puts it in a Mongo database.

The main components of Tesladata are the poller (poller.py) and the watcher (watcher.py).

## Poller
The poller component reads data from the Tesla API and stores it a Mongo database.

## Watcher
The watcher component connects to the Mongo database where the Poller stored the data and when a record is inserted, 'watcher' sends it to InfluxDB and publishes it on a MQTT topic.

The data is stored in InfluxDB so that it can be plotted with Grafana and published on MQTT for integration with Home-Assistant.

# Configuration
Edit the file `config.yaml`, the entries should be self-explanatory.

# Installation
Clone this repo and run `pip install -r requirements.txt` in the tesladata directory to install the rest of the Python requirements.

Run `make install` to install Tesladata on your system and start the poller service with the command `systemctl start tesladata-poller.service`

# MongoDB
Running a MongoDB can easily be done as a Docker container. To run a test database (the data will be lost when the container is stopped):

`docker run --rm --name mongodb -p 27017:27017 -d mongo --replSet rs0 --oplogSize 1024`

Or if you want to run it and store the data permantly, add a directory as a volume (this is how I run it):

`docker run --name mongodb -p 27017:27017 -v /my/own/datadir:/data/db -d mongo --replSet rs0 --oplogSize 1024`

## MongoDB replica set
When the MongoDB is started for the first time, you need to initiate a replica set. Do this with the command `rs.initiate()` in the mongo shell. To get a mongo shell on your docker container, run `sudo docker exec -ti mongodb mongo`

This replica set is needed, even if you have one MongoDB server, the Mongo function db.watch() we use, needs the MongoDB 'oplog' that is created/enabled when the recordset is initiated.

# Tools
## mongo-to-influxdb.py 
Read data from MongoDB and put it in InfluxDB. Use this to (re)fill InfluxDB with missing datapoints. 

Usage:

```lang=shell
./mongo-to-influxdb.py --configfile </path/to/config.yaml> --secondsback <integer>
```

The `secondsback` argument is used to generate a timestamp in milliseconds which is used to fetch documents from the MongoDB that are newer than that timestamp.

## mongo-dump.py
Read data from the MongoDB and return it as JSON on stdout

Usage
```lang=shell
usage: mongo-dump.py [-h] [--mongoserver MONGOSERVER] [--database DATABASE]
                    [--collection COLLECTION] [--diff]

optional arguments:
  --mongoserver     the mongoserver address [localhost]
  --database        the mongo database name where the Tesla data is [tesla]
  --collection      the mongo collection you want to see [all]
  --diff            show difference between stored data points [False]
```

## sleepy-to-sleeping.py
Measures the time between state 'sleepy' and 'asleep' and inserts the results in InfluxDB. Run this once per hour, missing datapoints can be inserted by running `mongo-to-influxdb.py`