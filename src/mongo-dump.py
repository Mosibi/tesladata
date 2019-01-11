#!/usr/bin/env python3

import time
import json
import argparse
from pymongo import MongoClient
from time import gmtime, strftime


def ms_to_date(ms):
    e = int(ms / 1000)
    t = time.localtime(e)
    return strftime("%a, %d %b %Y %H:%M:%S +0000", t)


def docdiff(current, previous):
    same = False
    if current == previous:
        same = True

    return same


def print_collection(collection, diff=False):
    coll = db[collection]
    documents = coll.find()

    for doc in documents:
        del doc["_id"]
        doc["timestamp"] = ms_to_date(doc["timestamp"])
        print(json.dumps(doc))

        try:
            if diff is True:
                for key in doc:
                    try:
                        if docdiff(doc[key], prev_doc[key]) is not True and not (
                            key == "timestamp" or key == "gps_as_of"
                        ):
                            # timestamp and gps_as_of are timestamps, those are most of the times different
                            # so let's skip them
                            print(
                                "diffent {}: {} vs previous {}".format(
                                    key, doc[key], prev_doc[key]
                                )
                            )
                    except KeyError as key:
                        print("found new key!: {}".format(key))
        except UnboundLocalError:
            pass

        prev_doc = doc


parser = argparse.ArgumentParser()
parser.add_argument(
    "--mongoserver",
    help="the mongoserver address, default localhost",
    default="localhost",
)
parser.add_argument(
    "--database",
    help="the mongo database name where the Tesla data is stored in, default tesla",
    default="tesla",
)
parser.add_argument(
    "--collection",
    help="the mongo collection you want to see, default is all",
    default="all",
)
parser.add_argument(
    "--diff", help="show difference between stored data points", action="store_true"
)

args = parser.parse_args()

client = MongoClient("mongodb://{}:27017/".format(args.mongoserver))
db = client[args.database]

print("Using mongoserver {} and database {}".format(args.mongoserver, args.database))

if args.collection == "all":
    for collection in db.list_collection_names():
        print_collection(collection, args.diff)
else:
    print_collection(args.collection, args.diff)
