#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

import argparse

from snmp_utils import Graph, Node, Router, Interface, Subnet, graph_to_graphmlfile
from copy import deepcopy
from netaddr import *
from net_functions import *

import common
import backend
import config
import time

parser = argparse.ArgumentParser(description="Create Network GraphML-File from Database")
parser.add_argument("--timestamp", help="Timestamp for getting data from backend")
parser.add_argument("--dst-host", nargs="?", default=config.data_backend_host, help="Backend database host")
parser.add_argument("--dst-port", nargs="?", default=config.data_backend_port, type=int, help="Backend database port")
parser.add_argument("--dst-user", nargs="?", default=config.data_backend_user, help="Backend database user")
parser.add_argument("--dst-password", nargs="?", default=config.data_backend_password, help="Backend database password")
parser.add_argument("--dst-database", nargs="?", default=config.data_backend_snmp_table, help="Backend database name")
parser.add_argument("--backend", nargs="?", default=config.data_backend, const=True, help="Selects the backend type that is used to store the data")

args = parser.parse_args()

dst_db = backend.databackend.getBackendObject(
        args.backend, args.dst_host, args.dst_port,
	args.dst_user, args.dst_password, args.dst_database)

# populate collections dictionary for easier access later on
#collections = {name: dst_db.getCollection(name) for name in ['ipRoute', 'interface_log', 'interface_perf', 'ipCidrRoute', 'cEigrp']}
collections = {name: dst_db.getCollection(name) for name in dst_db.getCollectionList()}

# if no timestamp was given used latest timestamp available
if args.timestamp:
	timestamp = args.timestamp
else:
	timestamp = sorted(collections['ipCidrRoute'].distinct("timestamp"), reverse=True)[0]

# function to check for graph irregularities
def do_checks(graph):
	print "Checking for interfaces without successor"
	for interface in graph.db["Interface"].itervalues():
		if len(interface.successors) == 0:
			print "Interface ohne Nachfolger: " + str(interface)

	print "Checking for unknown nodes"
	for node in graph.db["Node"].itervalues():
		if node.__class__ == Node:
			print "Unknown Node: " + str(node)

	print "Checking for wrongly assigned next hop nodes"
	for node in graph.db["Node"].itervalues():
		if node.__class__ == Node:
			for interface in graph.db["Interface"].itervalues():
				for ip in interface.ip:
					if node.ip == ip.split("/")[0]:
						print str(node.ip) + "/" + str(node.netmask) + " is not(!) unknown, belongs to " + str(interface) + node.reason_creation
	
	print "Checking for self-loop-nodes"
	for node in graph.db["Node"].itervalues():
		if node in node.successors:
			print "Self-loop-node " + str(node)



## create graph structure containing router and interfaces ##

graph = Graph()
print "Creating router and interfaces"

# add interfaces and routers to graph
for entry in collections['interface_log'].find({"timestamp": timestamp}):
	
	# convert from int to ip representation
	entry["ipAdEntAddr"] = int2ip(entry["ipAdEntAddr"])
	
	if_info = collections['interface_perf'].find({ 
		"router": entry["router"], "ifIndex": entry["ipAdEntIfIndex"], "timestamp": timestamp
	})[0]
	
	# add operational interface to graph
	if if_info["ifOperStatus"] == 1:
		graph.addInterface(
			entry["router"],
			entry["ipAdEntAddr"],
			entry["ipAdEntNetMask"],
			entry["ipAdEntIfIndex"],
			if_info["ifDescr"],
			str(entry)
		)


## create graph using ip route information ##

graph_copy = deepcopy(graph)
print "Creating route.local"

# parse local / direct routes
for entry in collections['ipCidrRoute'].find({"ipCidrRouteProto" : "2", "ipCidrRouteType" : "3", "timestamp": timestamp}):

	# convert from int to ip representation
	entry["ip_src"] = int2ip(entry["ip_src"])
	entry["ip_dst"] = int2ip(entry["ip_dst"])
	
	graph.addConnectedSubnetByNumber(
		entry["ip_src"],
		entry["ipCidrRouteIfIndex"],
		entry["ip_dst"],
		entry["mask_dst"],
		str(entry)
	)

# parse local / indirect route
for entry in collections['ipCidrRoute'].find({"ipCidrRouteProto": "3", "ipCidrRouteType" : "4", "timestamp": timestamp}):
#for entry in collections['ipCidrRoute'].find({"ipCidrRouteType" : "4", "timestamp": timestamp}):

	# convert from int to ip representation
	entry["ip_src"] = int2ip(entry["ip_src"])
	entry["ip_dst"] = int2ip(entry["ip_dst"])
	entry["ip_gtw"] = int2ip(entry["ip_gtw"])
	
	# determine interface to reach the new router (aka longest prefix matching)
	router_ip = IPAddress(entry["ip_gtw"])
	interface_number = None
	interface_netmask = None
	interface_netaddress = None
	
	interfaces = collections['interface_log'].find({"router": entry["ip_src"]}, sort={"ipAdEntNetMask": -1})
 
	for interface in interfaces:
		interface["ipAdEntAddr"] = int2ip(interface["ipAdEntAddr"])

		interface_network = IPNetwork(str(interface["ipAdEntAddr"]) + "/" + str(interface["ipAdEntNetMask"]))
		if (router_ip in interface_network):
			interface_netmask = interface["ipAdEntNetMask"]
			interface_number = interface["ipAdEntIfIndex"]
			interface_netaddress = interface_network.network
			break
	

	# add edge to next hop router
	if graph.isSubnet(interface_netaddress, interface_netmask):
		graph.addRoute_Subnet2Node(interface_netaddress, interface_netmask, entry["ip_gtw"])
	else:
		graph.addRoute_If2Node(entry["ip_src"], interface_number,
							   entry["ip_gtw"], 32, "55555")

	# add edge from next hop router to target network
	if int(entry["mask_dst"]) < 32:
		graph.addRoute_Node2Subnet(entry["ip_gtw"], 32, entry["ip_dst"], entry["mask_dst"])
	else:
		graph.addRoute_Node2Node(entry["ip_gtw"], 32, entry["ip_dst"], entry["mask_dst"])

print "Checking graph"
# do_checks(graph)
graph_to_graphmlfile(graph, "ba.route.local.graphml")

sys.exit(1)

## create eigrp grahp ##

graph = deepcopy(graph_copy)

print "Creating eigrp"

# add direct routes to subnet
for entry in collections['cEigrp'].find({"cEigrpRouteOriginType":"Connected"}):

	# convert from int to ip representation
	entry["ip_src"] = int2ip(entry["ip_src"])
	entry["ip_dst"] = int2ip(entry["ip_dst"])
	entry["cEigrpNextHopAddress"] = int2ip(entry["cEigrpNextHopAddress"])
	
	if_perf_info = collections['interface_perf'].find({"router": entry["ip_src"], "ifDescr": entry["cEigrpNextHopInterface"]})[0]
	if_log_info = collections['interface_log'].find({"router": entry["ip_src"], "ipAdEntIfIndex": if_perf_info["ifIndex"]})[0]

	graph.addConnectedSubnetByNumber(
		entry["ip_src"],
		if_log_info["ipAdEntIfIndex"],
		entry["ip_dst"],
		32 - int(entry["cEigrpDestNetPrefixLen"]),
		str(entry)
	)

# parse RStatic routes
for entry in collections['cEigrp'].find({"cEigrpRouteOriginType":"Rstatic"}):
	
	# convert from int to ip representation
	entry["ip_src"] = int2ip(entry["ip_src"])
	entry["ip_dst"] = int2ip(entry["ip_dst"])
	entry["cEigrpNextHopAddress"] = int2ip(entry["cEigrpNextHopAddress"])

	# determine interface to reach the new router (aka longest prefix matching)
	router_ip = IPAddress(entry["cEigrpNextHopAddress"])
	interface_number = None
	interface_netmask = None
	interface_netaddress = None
	
	for interface in (collections['interface_log'].find({"router": entry["ip_src"]}, sort={"ipAdEntNetMask", -1})):
		interface["ipAdEntAddr"] = int2ip(interface["ipAdEntAddr"])
		
		interface_network = IPNetwork(str(interface["ipAdEntAddr"]) + "/" + str(interface["ipAdEntNetMask"]))
		if (router_ip in interface_network):
			interface_netmask = interface["ipAdEntNetMask"]
			interface_number = interface["ipAdEntIfIndex"]
			interface_netaddress = interface_network.network
			break
			
	if graph.isSubnet(interface_netaddress, interface_netmask):
		graph.addRoute_Subnet2Node(interface_netaddress, interface_netmask, entry["cEigrpNextHopAddress"])
	else:
		graph.addRoute_If2Node(entry["ip_src"], interface_number, entry["cEigrpNextHopAddress"], 32, "55555")

	if int(entry["cEigrpRouteMask"]) < 32:
		graph.addRoute_Node2Subnet(entry["cEigrpNextHopAddress"], "32", entry["ip_dst"], 32 - int(entry["cEigrpDestNetPrefixLen"]))
	else:
		graph.addRoute_Node2Node(entry["cEigrpNextHopAddress"], "32", entry["ip_dst"], 32 - int(entry["cEigrpDestNetPrefixLen"]))

do_checks(graph)
graph_to_graphmlfile(graph, "ba.eigrp.graphml")

