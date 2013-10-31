#!/usr/bin/env python
# -*- coding: utf-8 -*-

# prepare paths
import sys
import os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

# import other modules
import common
import backend
import config

# import python modules
#import argparse
#import math
#import datetime
#import subprocess

class Importer:

	def __init__(self):
		pass

	def getNextDataSet(self):
		pass

class FlowBackendImporter(Importer):
	
	def __init__(self, last_timestamp = -1):
		# prepare database connection and create required collection objects
		self.db = backend.databackend.getBackendObject(config.data_backend, config.data_backend_host, config.data_backend_port, config.data_backend_user, config.data_backend_password, config.data_backend_snmp_name)
		self.tables = [self.db.getCollection("interface_phy"), self.db.getCollection("ifXTable")]
		
		### !!! ### DEBUG ### !!! ### 
#		last_timestamp = 1377201600

		# get all timestamps
		self.timestamps = set()
		for table in self.tables:
			self.timestamps.update(table.distinct("timestamp", {"timestamp": {"$gt": last_timestamp}}))
		self.timestamps = sorted(self.timestamps)

	def getNextDataSet(self):
		
		timestamp = self.timestamps.pop(0)
		self.last_timestamp = timestamp
		result = {}

		for table in self.tables:
#			db_result = table.find({"timestamp": timestamp, "router": "172.24.10.38", "if_number": "403767312"})
			db_result = table.find({"timestamp": timestamp})
			for data in db_result:

				try:
					result[data["router"]][data["if_number"]].update(data)
				except:
					try:
						result[data["router"]].update({
							data["if_number"]: data
						})
					except:
						result[data["router"]] = {
							data["if_number"]: data
						}
		return (timestamp, result)

	def __getinitargs__(self):
		return (self.last_timestamp,)

	def __getstate__(self):
		return {}


