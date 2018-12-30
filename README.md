# Tesladata
This toolset polls data from the Tesla API and places it in a Mongo database.

In the future I will also publish code that will read data from the Mongo database and put's it in an Influx database so it can be easily plotted with Grafana. 

# Configuration
Edit the file `config.yaml`, the entries should be self-explanatory.

# Installation
Clone this repo and install `teslajon` from https://github.com/gglockner/teslajson and follow the 'Installation' part. Then run `pip install -r requirements.txt` in the tesladata directory to install the rest of the Python requirements.

Run `make install` to install Tesladata on your system and start the poller service with the command `systemctl start tesladata-poller.service`

# MongoDB
Running a MongoDB can easily be done as a Docker container. To run a test database (the data will be lost when the container is stopped):

`docker run --rm --name mongodb -p 27017:27017 -d mongo`

Or if you want to run it and store the data permantly, add a directory as a volume (this is how I run it):

`docker run --name mongodb -p 27017:27017 -v /my/own/datadir:/data/db -d mongo`

