#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import argparse

import common
import backend
import config

import datetime

from prettytable import PrettyTable

from ordered_dict import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument("--router", default = "*")
parser.add_argument("--interface", default = "*")
parser.add_argument("--start_time", default = "18446744073709551615")
args = parser.parse_args()

db = backend.databackend.getBackendObject(config.data_backend, config.data_backend_host, config.data_backend_port, config.data_backend_user, config.data_backend_password, config.data_backend_snmp_name)
	
table_events = db.getCollection("events")
table_interface_phy = db.getCollection("interface_phy")
table_ifXTable = db.getCollection("ifXTable")

response = ""
keys = {}
limit_counter = 0
while True:

	if response == "n":
		limit_counter += 1
		response = ""

	if response == "":
		events = table_events.find({"mainid": args.router, "subid": args.interface}, sort = OrderedDict([("start_time", 0), ("mainid", 1), ("subid", 1)]), limit = str(limit_counter * 50) + ",50")

		pt = PrettyTable(["start_time", "end_time", "analyzer", "mainid", "subid", "eventtype", "description", "key"])
		pt.align["mainid"] = "l"
		pt.align["subid"] = "l"
		pt.align["description"] = "l"

		keys = {}
		counter = 0

		for event in events:
				counter += 1
				keys[str(counter)] = dict((key, event[key]) for key in ("start_time", "mainid", "subid", "analyzer", "eventtype"))
				pt.add_row([datetime.datetime.fromtimestamp(int(event['start_time'])), datetime.datetime.fromtimestamp(int(event['end_time'])), event['analyzer'], event['mainid'], event['subid'], event['eventtype'], event['description'], counter])
		print pt
	else:
		event = table_events.find(keys[response])[0]
		
		# print event
		pt = PrettyTable(["start_time", "end_time", "analyzer", "mainid", "subid", "eventtype", "description"])
		pt.align["mainid"] = "l"
		pt.align["subid"] = "l"
		pt.align["description"] = "l"
		pt.add_row([datetime.datetime.fromtimestamp(int(event['start_time'])), datetime.datetime.fromtimestamp(int(event['end_time'])), event['analyzer'], event['mainid'], event['subid'], event['eventtype'], event['description']])
		print pt
		
		# print details from measurements
		detail_data = {
			"interface_phy": ["ifAdminStatus", "ifOperStatus", "ifOutUcastPkts"],
			"ifXTable": ["ifHCOutUcastPkts"]
		}

		for table, columns in detail_data.iteritems():
			# get collection
			db_table = db.getCollection(table)

			# find timestamps before and after event timestamp
			low_time = db_table.find({"timestamp": {"$lt": event["start_time"]}, "router": event["mainid"], "if_number": event["subid"]}, {"distinct timestamp": 1}, sort = {"timestamp": 0}, limit = 2)[1]["timestamp"]
			high_time = db_table.find({"timestamp": {"$gt": event["end_time"]}, "router": event["mainid"], "if_number": event["subid"]}, {"distinct timestamp": 1}, sort = {"timestamp": 1}, limit = 2)[1]["timestamp"]

			# prepare and print table
			print "\nData from " + table + ":"
			pt = PrettyTable(["timestamp"] + columns)
			data = db_table.find({"timestamp": {"$gte": low_time}, "Timestamp": {"$lte": high_time}, "router": event["mainid"], "if_number": event["subid"]})
			for row in data:
				pt.add_row([datetime.datetime.fromtimestamp(int(row['timestamp']))] + [row[field] for field in columns])
			print pt
	
	response = raw_input()
