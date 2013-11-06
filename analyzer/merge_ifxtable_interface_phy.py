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
args = parser.parse_args()

db = backend.databackend.getBackendObject(config.data_backend, config.data_backend_host, config.data_backend_port, config.data_backend_user, config.data_backend_password, config.data_backend_snmp_table)
	
table_interface_phy = db.getCollection("interface_phy")
table_ifXTable = db.getCollection("ifXTable")
table_interface_perf = db.getCollection("interface_perf")

timestamps = set()
timestamps.update(table_interface_phy.distinct("timestamp"))
timestamps.update(table_ifXTable.distinct("timestamp"))
timestamps = sorted(timestamps)

for timestamp in timestamps:
	print datetime.datetime.fromtimestamp(timestamp)

	commit_doc = {}

	db_result = table_interface_phy.find({"timestamp": timestamp})
	for result in db_result:
		try:
			commit_doc[str(result['timestamp']) + '-' + str(result['router']) + '-' + str(result['if_number'])].update(dict(result))
		except KeyError:
			commit_doc[str(result['timestamp']) + '-' + str(result['router']) + '-' + str(result['if_number'])] = dict(result)

	db_result = table_ifXTable.find({"timestamp": timestamp})
	for result in db_result:
		try:
			commit_doc[str(result['timestamp']) + '-' + str(result['router']) + '-' + str(result['if_number'])].update(dict(result))
		except KeyError:
			commit_doc[str(result['timestamp']) + '-' + str(result['router']) + '-' + str(result['if_number'])] = dict(result)

	for key, data in commit_doc.iteritems():
		table_interface_perf.update({}, {"$set": data})

table_interface_perf.flushCache()
