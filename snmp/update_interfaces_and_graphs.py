#!/usr/bin/env python

'''
This script configures the graphs and stuff that are needed by the
external web app (not included in this source code tree yet). 

@author: braun
'''

import sys
import os.path
import subprocess
import time
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vendor'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

import config
import common
import backend
import csv_configurator
import snmp_preprocess
import config_snmp_dump

def create_cpu_list(cpu_coll):
	# creating CPU tables
	print "Retrieving CPU infos"
	cisco_cpu_coll = dst_db.getCollection("ciscoCpu")
	cpu_list_coll = dst_db.getCollection('cpu_list')
	resultSet = cisco_cpu_coll.find({}, fields={"DISTINCT ROUTER": 1, "CPU_NUMBER": 1})
	for i in resultSet:
		print i
		ip = i["ROUTER"]
		if not ip in device_list:
			print "ERROR: Device %s has CPU statistics but does not have any interface stats!"
			continue
		device_id = device_list[ip]['r_id']
# get device id in snmp_dev_coll for router
		
		doc = dict()
		table_entry = { 'NOTE': ""}
		doc["$set"] = table_entry
		cpu_list_coll.update({ "DEVICE_ID": device_id, "CPU_NUMBER": i["CPU_NUMBER"]}, doc)
	cpu_list_coll.flushCache()

def create_mem_list(mem_coll):
	# creating MEM tables
	print "Retrieving MEM infos"
	cisco_mem_coll = dst_db.getCollection("ciscoMemory")
	mem_list_coll = dst_db.getCollection('mem_list')
	resultSet = cisco_mem_coll.find({}, fields={"DISTINCT ROUTER": 1, "POOL_NUMBER": 1})
	for i in resultSet:
		ip = i["ROUTER"]
		if not ip in device_list:
			print "ERROR: Device %s has MEM statistics but does not have any interface stats!"
			continue
		device_id = device_list[ip]['r_id']
	# get device id in snmp_dev_coll for router
		doc = dict()
		table_entry = { 'NOTE': ""}
		doc["$set"] = table_entry
		mem_list_coll.update({ "DEVICE_ID": device_id, "POOL_NUMBER": i["POOL_NUMBER"]}, doc)
	print "Flushing memory cache..."
	mem_list_coll.flushCache()

def create_interface_list(device_coll, interface_phy_coll, ifxtable_coll, destination_coll):
	"""
	Extract all devices that are known to ifXTable and interface_phy.
	Merge their values (e.g. status, if_names) into a consistent view
	and store this view in the database for quick access by the web
	frontend application.
	"""
	print "Fetching list of devices and interfaces from ifxTable ..."
	interface_results = ifxtable_coll.find({}, fields={"DISTINCT router" : 1, "if_number" : 1, 'ifName': 1, 'ifAlias': 1})

	print "Fetching list of interface statuses ..."
	iface_phy_results = interface_phy_coll.find({}, fields={"DISTINCT router" : 1, "if_number" : 1, "ifOperStatus": 1, "ifType":1})

	print "Retrieving a list of device ids ..."
	deviceresults = device_coll.find({}, fields={"ip": 1, "_id": 1})
	device_map = dict()
	for result in deviceresults:
		device_map[result['ip']] = result['_id']

	interface_list = {}
	for res in interface_results:
		interface_list_entry = dict()
		if_number = res['if_number']
		ip = res['router']
		if_id = ip + "_" + str(if_number)
		if if_id in interface_list:
			# duplicates can occur. E.g. when an alias or name of the interface was changed by an operator
			# we need some error handling to get the latest value for ifName and ifAlias
			# TODO: implement error handling. for now we just take the update and discard the old value
			pass
			#print "FATAL: Found duplicate interface in interface_list.\nFATAL: Old Entry: ", interface_list[if_id], '\nFATAL: New entry: ', res
			#sys.exit(-1)
		if not ip in device_map:
			print "FATAL: Found IP \"" + ip + "\" in interface_results but IP is not known in device_map"
			sys.exit(-2)
		interface_list_entry['device_id'] = device_map[ip]
		interface_list_entry['if_number'] = res['if_number']
		interface_list_entry['if_alias']  = res['ifAlias']
		interface_list_entry['if_name']   = res['ifName']
		interface_list[if_id] = interface_list_entry
	# we now have the basic information for the interfaces. 
	# we now want to enrich this informaiton with the interface status from interface_phy_results
	for res in iface_phy_results:
		if_number = res['if_number']
		ip = res['router']
		if_id = ip + "_" + str(if_number)
		if not if_id in interface_list:
			print "FATAL: Found an interface in interface_list (ifXTable) that does not have a corresponding interface in (interface_phy):", res
			continue
		interface_list[if_id]['if_status'] = res['ifOperStatus']
		interface_list[if_id]['if_type'] = res['ifType']
	print "Pushing data into database..."
	for if_id in interface_list:
		interface = interface_list[if_id]
		device_id = interface['device_id']
		if_number = interface['if_number']
		del interface['device_id']
		del interface['if_number']
		doc = dict()
		doc["$set"] = interface
		destination_coll.update({'device_id': device_id, 'if_number' : if_number}, doc)
	destination_coll.flushCache()
		

def create_graph_templates(collection):
	"""
	Insert graph configs from config_snmp_dump into the collection
	"""
	for graph in config_snmp_dump.graph_dict:
		graph_config = config_snmp_dump.graph_dict[graph]
		for item in graph_config:
			(field1, field2, title, vert_label, scale) = item
			doc = dict()
			table_entry = dict()
			table_entry["type"] = graph
			table_entry["field1"] = field1
			table_entry["field2"] = field2
			table_entry["vert_legend"] = vert_label
			table_entry["scale"] = scale
			table_entry["start_time"] = -86400
			table_entry["end_time"] = -300
			doc["$set"] = table_entry
			collection.update({"graph_name": title}, doc)
	collection.flushCache()


if __name__ == "__main__":
	parser = common.get_default_argument_parser("Tool for performing live checks on the devices that require the monitoring")

	args = parser.parse_args()

	dst_db = backend.databackend.getBackendObject(
		args.backend, args.dst_host, args.dst_port,
		args.dst_user, args.dst_password, args.dst_database)

	measurement_map_filename =  os.path.join(os.path.dirname(__file__), "..", "config",  "monitoring_devices.csv")
	for name, fields in csv_configurator.read_field_dict_from_csv(args.backend, measurement_map_filename).items():
		dst_db.prepareCollection(name, fields)
	snmp_preprocess.prepare_snmp_collections(dst_db, args.backend)

	create_graph_templates(dst_db.getCollection("graph_list"))

	device_coll = dst_db.getCollection("device_table")
	interface_phy_coll = dst_db.getCollection("interface_phy")
	ifxtable_coll = dst_db.getCollection("ifXTable")
	destination_coll = dst_db.getCollection("interface_list")
	cpu_list = dst_db.getCollection('ciscoCpu')
	mem_list = dst_db.getCollection('ciscoMemory')

	create_interface_list(device_coll, interface_phy_coll, ifxtable_coll, destination_coll)
	create_cpu_list(cpu_list)
	create_mem_list(mem_list)
	
	
