if(!FlowInspector) {
	var FlowInspector = {};
}

// definitions
/*
FlowInspector.tcpColor = "rgba(204,0,0,1.0)"
FlowInspector.udpColor = "rgba(0,204,0,1.0)"
FlowInspector.icmpColor = "rgba(0,102,204,1.0)"
FlowInspector.otherColor = "rgba(255,163,71,1.0)"
*/
FlowInspector.tcpColor = "rgb(204,0,0)";
FlowInspector.udpColor = "rgb(0,204,0)";
FlowInspector.icmpColor = "rgb(0,102,204)";
FlowInspector.otherColor = "rgb(255,163,71)";

FlowInspector.COL_FIRST_SWITCHED = "flowStartSeconds"
FlowInspector.COL_LAST_SWITCHED = "flowEndSeconds"
// column names of IP addresses
FlowInspector.COL_SRC_IP = "sourceIPv4Address"
FlowInspector.COL_DST_IP = "destinationIPv4Address"

// column names for indexes (bidirectional)
FlowInspector.COL_IPADDRESS = "ipaddress"
FlowInspector.COL_PORT = "port"

// column names of ports and protocol
FlowInspector.COL_SRC_PORT = "sourceTransportPort"
FlowInspector.COL_DST_PORT = "destinationTransportPort"
FlowInspector.COL_PROTO = "protocolIdentifier"
FlowInspector.COL_BUCKET = "bucket"


FlowInspector.COL_BYTES = "octetDeltaCount"
FlowInspector.COL_PKTS = "packetDeltaCount"
FlowInspector.COL_FLOWS = "flows"
FlowInspector.COL_ID = "id"

FlowInspector.COL_PROTO_TCP = "tcp"
FlowInspector.COL_PROTO_UDP = "udp"
FlowInspector.COL_PROTO_ICMP = "icmp"
FlowInspector.COL_PROTO_OTHER = "other"



/**
 * Transforms a 32bit IPv4 address into a human readable format
 * (e.g. 192.168.0.1)
 */
FlowInspector.ipToStr = function(ip) {
	return (ip >>> 24) + "." +
		   (ip >> 16 & 0xFF) + "." +
		   (ip >> 8 & 0xFF) + "." +
		   (ip & 0xFF);
};

/**
 * Transforms a human readable IPv4 address into a 32bit integer
 * (e.g. 192.168.0.1)
 */
FlowInspector.strToIp = function(str) {
	var parts = str.split(".");
	if(parts.length !== 4) {
		return null;
	}
	
	var ip = 0;
	for(var i = 0; i < 4; i++) {
		var j = parseInt(parts[i]);
		// check for range and Nan
		if(j !== j || j < 0 || j > 255) {
			return null;
		}
		ip = (ip << 8) + j;
	}
	return (ip >>> 0);
};

/**
 * Functions to work with Hilbert Curves.
 * (http://en.wikipedia.org/wiki/Hilbert_curve)
 */
 
//convert (x,y) to d
FlowInspector.hilbertXY2D = function(n, x, y) {
    var rx, ry, s, r, d = 0;
    for(s = n/2; s > 0; s /= 2) {
        rx = (x & s) > 0;
        ry = (y & s) > 0;
        d += s * s * ((3 * rx) ^ ry);
        r = FlowInspector.hilbertRot(s, x, y, rx, ry);
        x = r.x;
        y = r.y;
    }
    return d;
};
 
//convert d to (x,y)
FlowInspector.hilbertD2XY = function(n, d) {
    var rx, ry, s, r, t = d;
    var x = 0, y = 0;
    for(s = 1; s < n; s *= 2) {
        rx = 1 & (t/2);
        ry = 1 & (t ^ rx);
        r = FlowInspector.hilbertRot(s, x, y, rx, ry);
        x = r.x;
        y = r.y;
        x += s * rx;
        y += s * ry;
        t /= 4;
    }
    return { x: x, y: y };
};
 
//rotate/flip a quadrant appropriately
FlowInspector.hilbertRot = function(n, x, y, rx, ry) {
    var t;
    if(ry == 0) {
        if(rx == 1) {
            x = n-1 - x;
            y = n-1 - y;
        }
        t  = x;
        x = y;
        y = t;
    }
    return { x: x, y: y };
};

FlowInspector.isIPValid = function(ipaddr)  {
	// remove any spaces
	ipaddr = ipaddr.replace( /\s/g, "");
	// check for ipv4 address and optional subnet mask
	var re = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/;

	if (re.test(ipaddr)) {
		var  mask, parts;
		// get address and subnet mask
		parts = ipaddr.split("/");
		ipaddr = parts[0];

		if (parts[1] != "") {
			// if mask has been given, check if it is a valid mask
			mask = parseInt(parts[1], 10);
			if (mask == NaN || mask < 0 || mask > 32) {
				 // not a valid subnet mask
				return false;
			}
		}
		// check if address is valid
		parts = ipaddr.split(".");
		for (var i = 0; i < parts.length; ++i) {
			var num = parseInt(parts[i]);
			if (parts[i] == NaN || parts[i] < 0 || parts[i] > 255) {
				return false
			}	
		}
		return true;
        }
	return false;
}

FlowInspector.getTitleFormat = function(value, protocol) {
	if(value === FlowInspector.COL_PKTS) {
		return function(d) { 
			var val = 0;
			// if get is a function, call it, otherwise take d's value
			if (protocol  !== undefined) {
				var pSpecific = d.get(protocol);
				if (pSpecific !== undefined) {
					val = d.get(protocol)[value];
				} else {
					val = 0;
				}
			} else if (typeof d.get == 'function') {
				val = d.get(value);
			} else {
				val = d;
			}
			var factor = 1;
			var unit = "";
			if (val >= 1000*1000) {
				factor = 1000 * 1000;
				unit = "m";
			} else if (val >= 1000) {
				factor = 1000;
				unit = "k";
			}
			return Math.floor(val/factor)+unit; };
	}
	if(value === FlowInspector.COL_BYTES) {
		return function(d) { 
			var val = 0;
			// if get is a function, call it, otherwise take d's value
			if (protocol  !== undefined) {
				var pSpecific = d.get(protocol);
				if (pSpecific !== undefined) {
					val = d.get(protocol)[value];
				} else {
					val = 0;
				}
			} else if (typeof d.get == 'function') {
				val = d.get(value);
			} else {
				val = d;
			}
			var factor = 1;
			var unit = "B"
			// bigger than terrabyte
			if (val > 1000*1000*1000*1000) {
				factor = 1000*1000*1000*1000;
				unit = "TB";
			} else if (val > 1000*1000*1000) {
				factor = 1000*1000*1000;
				unit = "GB";
			} else if (val > 1000*1000) {
				factor = 1000*1000;
				unit = "MB";
			} else if (val > 1000) {
				factor = 1000;
				unit = "kB";
			} else {
				return (d3.format("f"))(val) + unit;
			}

			return (d3.format(".2f"))(val/factor) + unit; };
	}
	return function(d) { 
		var val = 0;
		// if get is a function, call it, otherwise take d's value
		if (protocol  !== undefined) {
			var pSpecific = d.get(protocol);
			if (pSpecific !== undefined)  {
				val = d.get(protocol)[value];
			} else {
				val = 0;
			}
		} else 	if (typeof d.get == 'function') {
			val = d.get(value);
		} else {
			val = d;
		}
		return Math.floor(val)  };
}

FlowInspector.addToFilter = function(data, model, aggregate_fields, always_aggregate) {
	var filter_ports = model.get("filterPorts");
	var filter_ports_type = model.get("filterPortsType");
	var filter_ips = model.get("filterIPs");
	var filter_ips_type = model.get("filterIPsType");
	var filter_protocols = model.get("filterProtocols");
	var filter_protocols_type = model.get("filterProtocolsType");
	var do_aggregate = false;


	// apply filter for ports
	var ports = filter_ports.split("\n");
	filter_ports = "";
	for(var i = 0; i < ports.length; i++) {
		var p = parseInt(ports[i]);
		// test for NaN
		if(p === p) {
			if (p < 0 || p > 65535) {
				alert("Illegal port \"" + p + "\" in port filter list!");
				return null;
			}
			if(filter_ports.length > 0) {
				filter_ports += ",";
			}
			filter_ports += p;
		} else {
			if (ports[i] !== "") {
				alert("Illegal value in \"" + ports[i] + "\" in port filter list!");
				return null;
			}
		}
	}
	if(filter_ports) {
		if(filter_ports_type === "exclusive") {
			data["exclude_ports"] = filter_ports;
		} else {
			data["include_ports"] = filter_ports;
		}
		do_aggregate = true;
	}

	// apply filter for IPs
	var ips = filter_ips.split("\n");
	filter_ips = "";
	for(var i = 0; i < ips.length; i++) {
		var p = FlowInspector.strToIp(ips[i]);
		if(p != null) {
			if(filter_ips.length > 0) {
				filter_ips += ",";
			}
			filter_ips += p;
		} else {
			if (ips[i] !== "") {
				alert("Illegal value \"" + ips[i] + "\" in IP filter list. Please specify your IP address in dotted notation. We do not yet support subnets in IP filters. Sorry! :/");
				return null;
			}
		}
	}
	if(filter_ips) {
		if(filter_ips_type === "exclusive") {
			data["exclude_ips"] = filter_ips;
		} else {
			data["include_ips"] = filter_ips;
		}
		do_aggregate = true;
	}

	// apply filter for protocols
	var protocols = filter_protocols.split("\n");
	filter_protocols = "";
	for(var i = 0; i < protocols.length; i++) {
		var value = protocols[i].toLowerCase();
		if (value !== FlowInspector.COL_PROTO_TCP && value !== FlowInspector.COL_PROTO_UDP && value !== FlowInspector.COL_PROTO_ICMP && value !== FlowInspector.COL_PROTO_OTHER && value !== "") {
			alert("Not supported protocol \"" + value + "\" in protocol list. We support " + FlowInspector.COL_PROTO_TCP + ", " + FlowInspector.COL_PROTO_UDP + ", " + FlowInspector.COL_PROTO_ICMP + ", and " + FlowInspector.COL_PROTO_OTHER + " at the moment.");
			return null;

		}
		if(filter_protocols.length > 0) {
			filter_protocols += ",";
		}
		filter_protocols += value;
	}
	if(filter_protocols) {
		if(filter_protocols_type === "exclusive") {
			data["exclude_protos"] = filter_protocols;
		} else {
			data["include_protos"] = filter_protocols;
		}
		do_aggregate = true;
	}


	// we need to calculate the buckets dynamically 
	// because of dynamic filtering. Prepare the 
	// query that does the aggregation on the default
	// non-aggregated db
	if (do_aggregate || always_aggregate) {
		data["aggregate"] = aggregate_fields
	}

	
	return data;
}

