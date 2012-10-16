"""
Backend wrappers. Select and create the appropriate objects for 
backend communication.

Currently supported backends:
	- mongodb
	- mysql
	- oracle

Author: Lothar Braun 
"""

import sys
import config
import common

class Collection:
	"""
		This class is a wrapper for the mongo db collection classes
		it takes requests for storing and querying data from the
		application and passes it to the backend classes, which are
		then responsible for storing and retriving the data in/from 
		the actual database.
		For backends other than mongo, a collection represents a 
		table (SQL) or another appropriate collection for flows that
		belong to the same cagegory
	"""
	def __init__(self, backendObject, collectionName):
		self.backendObject = backendObject
		self.collectionName = collectionName
		self.name = collectionName

	def createIndex(self, fieldName):
		"""
		Creates an index on the given field if the database 
		supports indexes
		"""
		self.backendObject.createIndex(self.collectionName, fieldName)

	def update(self, statement, document, insertIfNotExist):
		"""
		Updates or creates a flow in the database. 
		- statement - contains the id of the flow in the database (_id for mongo, primary key for sql)
		- document - contains the properties of the flow
		- insertIfNotExist: true: insert flow into db if it doesn't exist; false: only update entries of existing flows, do not create new flow
		"""
		self.backendObject.update(self.collectionName, statement, document, insertIfNotExist)

	def bucket_query(self, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		"""
		Queries the database for a set of flows that match the given properties
		- spec - mongo specific spec for the query. already encodes the arguments (applies only to mongo)
		- fields - database fields that should be queried and returned by the database
		- sort - list of fields that should be sorted, including the sort direction
		- count - maximum number of flows that should be returned
		- startBucket: start interval for flows
		- endBucket: end interval for flow queries
		- resolution: desired time resolution
		- bucketSize: size of buckets to be queried
		- biflow: whether we should have biflow aggregation or not
		- includePorts: only select flows that involve the ports in this list
		- excludePorts: only select flows that do not involve the ports in this list
		- inludeIPs: only select flows that involve the ips in this list
		- excludeIPs: only select flows that do not involve the ips in this list
		- batchSize: database should select the flows in batch sizes of batchSize (ignored for most backends)
		"""
		return self.backendObject.bucket_query(self.collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)

	def index_query(self, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		"""
		Queries the database for static indexes on all flows in the database
		- spec - mongo specific spec for the query. already encodes the arguments (applies only to mongo)
		- fields - database fields that should be queried and returned by the database
		- sort - list of fields that should be sorted, including the sort direction
		- count - maximum number of flows that should be returned
		- startBucket: start interval for flows
		- endBucket: end interval for flow queries
		- resolution: desired time resolution
		- bucketSize: size of buckets to be queried
		- biflow: whether we should have biflow aggregation or not
		- includePorts: only select flows that involve the ports in this list
		- excludePorts: only select flows that do not involve the ports in this list
		- inludeIPs: only select flows that involve the ips in this list
		- excludeIPs: only select flows that do not involve the ips in this list
		- batchSize: database should select the flows in batch sizes of batchSize (ignored for most backends)
		"""
		return self.backendObject.index_query(self.collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)
 
	def dynamic_index_query(self, name, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		"""
		Queries the database for dynamic indexes which are calculated based on the start and end intervals
		- name - index name (ports or nodes)
		- spec - mongo specific spec for the query. already encodes the arguments (applies only to mongo)
		- fields - database fields that should be queried and returned by the database
		- sort - list of fields that should be sorted, including the sort direction
		- count - maximum number of flows that should be returned
		- startBucket: start interval for flows
		- endBucket: end interval for flow queries
		- resolution: desired time resolution
		- bucketSize: size of buckets to be queried
		- biflow: whether we should have biflow aggregation or not
		- includePorts: only select flows that involve the ports in this list
		- excludePorts: only select flows that do not involve the ports in this list
		- inludeIPs: only select flows that involve the ips in this list
		- excludeIPs: only select flows that do not involve the ips in this list
		- batchSize: database should select the flows in batch sizes of batchSize (ignored for most backends)
		"""
		return self.backendObject.index_query(self.collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)
 

	def find_one(self, spec, fields=None, sort=None):
		return self.backendObject.find_one(self.collectionName, spec, fields, sort)

	def flushCache(self, collectionName = None):
		return self.backendObject.flushCache(collectionName)

class Backend:
	def __init__(self, host, port, user, password, databaseName):
		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self.databaseName = databaseName

	def connect(self):
		pass

	def getMinBucket(self, bucketSize = None):
		"""
		Gets the earliest bucket that is stored in the database for the given 
		bucket size. 
		"""
		pass

	def getMaxBucket(self, bucketSize = None):
		"""
		Gets the latest bucket that is stored in the database for the given 
		bucket size. 
		"""
		pass


	def getBucketSize(self, startTime, endTime, resolution):
		"""
		Calculates the bucket size that is closest to the requested resolution.
		The resolution is specified by the javascript client application and
		can be picked to be an arbitrary value.
		The bucket sizes are defined in config.py, and must not necessarily
		match to the requested resolution.
		"""
		pass

	def clearDatabase(self):
		"""
		Removes all data from the backend
		"""
		pass

	def getCollection(self, name):
		"""
		Creates and returns a wrapper "Collection" object which represents
		a collection/table in the database. 
		"""
		return Collection(self, name)
	
	def prepareCollections(self):
		"""
		This method is responsible for initializing the database on application 
		start. Some databases need to create tables when the database is used
		for the first time. Others require maintainance or sanity checking on 
		before the database can be used (e.g. writes). 
		All such initialization is done in this method. The method is only 
		called for writing processes (e.g. the preprocessor)
		"""
		pass

	def createIndex(self, collectionName, fieldName):
		"""
		Creates an index on the collection/table "collectionName" on the
		field "fieldName", if the database supports creating indexes.
		"""
		pass

	def update(self, collectionName, statement, document, insertIfNotExists):
		"""
		Adds or updates a flow in the collection "collectionName". See class
		Collection for full documentation. 
		"""
		pass

	def flushCache(self, collectionName=None):
		"""
		If the backend decides to have a separate cache, this method can be used
		to flush the cache. It will be called by the preprocessing scripts as
		soon as the script finishes.
		- collectionName: optional, if defined, only the collection with name "collectionName" 
		  		  will be flushed. If value is None, all collections are flushed and 
				  written to db.
		"""
		pass

	def bucket_query(self, collectionName,  spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		"""
		Queries flows from the database and collection "colletionName". See
		class Collection for full documentation of the parameters.
		"""
		pass

	def index_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		"""
		Queries static indexes on the full database. See class Collection for 
		full documentation.
		"""
		pass

	def dynamic_index_query(self, name, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		pass 
	
	def find_one(self, collectionName, spec, fields, sort):
		pass

	def run_query(self, collectionName, query):
		pass


class MongoBackend(Backend):
	def __init__(self, host, port, user, password, databaseName):
		Backend.__init__(self, host, port, user, password, databaseName)
		self.connect()

	def connect(self):
		# init pymongo connection
		try:
			import pymongo
		except Exception as inst:
			print >> sys.stderr, "Cannot connect to Mongo database: pymongo is not installed!"
			sys.exit(1)
		try:
			self.conn = pymongo.Connection(self.host, self.port)
		except pymongo.errors.AutoReconnect, e:
			print >> sys.stderr, "Cannot connect to Mongo Database: ", e
			sys.exit(1)
		self.dst_db = self.conn[self.databaseName]
	

	def getMinBucket(self, bucketSize = None):
		import pymongo
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		coll = self.dst_db[common.DB_FLOW_PREFIX + str(bucketSize)]
		min_bucket = coll.find_one(
			fields={ "bucket": 1, "_id": 0 }, 
			sort=[("bucket", pymongo.ASCENDING)])
		return min_bucket["bucket"]

	def getMaxBucket(self, bucketSize = None):
		import pymongo
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		coll = self.dst_db[common.DB_FLOW_PREFIX + str(bucketSize)]
		max_bucket = coll.find_one(
			fields={ "bucket": 1, "_id": 0 }, 
			sort=[("bucket", pymongo.DESCENDING)])
		return max_bucket["bucket"]


	def getBucketSize(self, start_time, end_time, resolution):
		import pymongo
		for i,s in enumerate(config.flow_bucket_sizes):
			if i == len(config.flow_bucket_sizes)-1:
				return s
				
			coll = self.getCollection(common.DB_FLOW_AGGR_PREFIX + str(s))
			min_bucket = coll.find_one(
				{ "bucket": { "$gte": start_time, "$lte": end_time} }, 
				fields={ "bucket": 1, "_id": 0 }, 
				sort=[("bucket", pymongo.ASCENDING)])
			max_bucket = coll.find_one(
				{ "bucket": { "$gte": start_time, "$lte": end_time} }, 
				fields={ "bucket": 1, "_id": 0 }, 
				sort=[("bucket", pymongo.DESCENDING)])
				
			if not min_bucket or not max_bucket:
				return s
			
			num_slots = (max_bucket["bucket"]-min_bucket["bucket"]) / s + 1
			if num_slots <= resolution:
				return s

	
	def clearDatabase(self):
		self.conn.drop_database(self.databaseName)


	def createIndex(self, collectionName, fieldName):
		collection = self.dst_db[collectionName]
		collection.create_index(fieldName)

	def update(self, collectionName, statement, document, insertIfNotExists):
		collection = self.dst_db[collectionName]
		collection.update(statement, document, insertIfNotExists)

	def bucket_query(self, collectionName,  spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		import pymongo
		collection = self.dst_db[collectionName]
		cursor = collection.find(spec, fields=fields).batch_size(1000)
		if sort: 
			cursor.sort("bucket", sort)
		else:
			cursor.sort("bucket", pymongo.ASCENDING)

		buckets = []
		if (fields != None and len(fields) > 0) or len(includePorts) > 0 or len(excludePorts) > 0 or len(includeIps) > 0 or len(excludeIps) > 0:
			current_bucket = -1
			aggr_buckets = {}
			for doc in cursor:
				if doc["bucket"] > current_bucket:
					for key in aggr_buckets:
						buckets.append(aggr_buckets[key])
					aggr_buckets = {}
					current_bucket = doc["bucket"]
					
				# biflow?
				if biflow and common.COL_SRC_IP in fields and common.COL_DST_IP in fields:
					srcIP = doc.get(common.COL_SRC_IP, None)
					dstIP = doc.get(common.COL_DST_IP, None)
					if srcIP > dstIP:
						doc[common.COL_SRC_IP] = dstIP
						doc[common.COL_DST_IP] = srcIP
				
				# construct aggregation key
				key = str(current_bucket)
				for a in fields:
					key += str(doc.get(a, "x"))
				
				if key not in aggr_buckets:
					bucket = { "bucket": current_bucket }
					for a in fields:
						bucket[a] = doc.get(a, None)
					for s in ["flows"] + config.flow_aggr_sums:
						bucket[s] = 0
					aggr_buckets[key] = bucket
				else:
					bucket = aggr_buckets[key]
				
				for s in ["flows"] + config.flow_aggr_sums:
					bucket[s] += doc.get(s, 0)
				
			for key in aggr_buckets:
				buckets.append(aggr_buckets[key])
		else:
			# cheap operation if nothing has to be aggregated
			for doc in cursor:
				del doc["_id"]
				buckets.append(doc)
		return buckets

	def index_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		collection = self.dst_db[collectionName]
		# query without the total field	
		full_spec = {}
		full_spec["$and"] = [
				spec, 
				{ "_id": { "$ne": "total" }}
			]
	
		cursor = collection.find(full_spec, fields=fields).batch_size(1000)
	
		if sort:
			cursor.sort(sort)
		if limit:
			cursor.limit(limit)
			
		if count:
			result = cursor.count() 
		else:
			result = []
			total = []
			for row in cursor:
				row["id"] = row["_id"]
				del row["_id"]
				result.append(row)
	
		# get the total counter
		spec = {"_id": "total"}
		cursor = collection.find(spec)
		if cursor.count() > 0:
			total = cursor[0]
			total["id"] = total["_id"]
			del total["_id"]
	
		return (result, total)

	def dynamic_index_query(self, name, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		def createNewIndexEntry(row):
			# top level
			r = { "id": row[key[0]], "flows": 0 }
			for s in config.flow_aggr_sums:
				r[s] = row[s]
	
			# protocol specific
			for p in common.AVAILABLE_PROTOS:
				r[p] = { "flows": 0 }
				for s in config.flow_aggr_sums:	
					r[p][s] = 0
			# src and dst specific		
			for dest in ["src", "dst"]:
				r[dest] = {}
				r[dest]["flows" ] = 0
				for s in config.flow_aggr_sums:
					r[dest][s] = 0
			return r

		collection = db.getCollection(common.DB_FLOW_PREFIX + str(bucket_size))
	
		cursor = collection.find(spec, fields=fields).batch_size(1000)
	
		result = {}

		# total counter that contains information about all flows in 
		# the REQUESTED buckets (not over the complete dataset)
		# this is important because the limit parameter might remove
		# some information
		total = {}
		total["flows"] = 0
		for s in config.flow_aggr_sums:
			total[s] = 0
		for proto in common.AVAILABLE_PROTOS:
			total[proto] = {}
			total[proto]["flows"] = 0
			for s in config.flow_aggr_sums:
				total[proto][s] = 0
	
		for row in cursor:
			if name == "nodes":
				keylist = [ (common.COL_SRC_IP, "src"), (common.COL_DST_IP, "dst") ]
			elif name == "ports":
				keylist = [ (common.COL_SRC_PORT, "src"), (common.COL_DST_PORT, "dst") ]
			else:
				raise HTTPError(output = "Unknown dynamic index")
	
			# update total counters
			total["flows"] += row["flows"]
			if common.COL_PROTO in row:
				total[common.getProtoFromValue(row[common.COL_PROTO])]["flows"] += row["flows"]
			for s in config.flow_aggr_sums:
				total[s] += row[s]
				if common.COL_PROTO in row:
					total[common.getProtoFromValue(row[common.COL_PROTO])][s] += row[s]
	
	
			# update individual counters
			for key in keylist:
				if row[key[0]] in result:
					r = result[row[key[0]]]
				else:
					r = createNewIndexEntry(row)
	
				r["flows"] += row["flows"]
				r[key[1]]["flows"] += row["flows"]
				for s in config.flow_aggr_sums:
					r[s] += row[s]
					r[key[1]][s] += row[s]
	
				if common.COL_PROTO in row:
					r[common.getProtoFromValue(row[common.COL_PROTO])]["flows"] += row["flows"]
					for s in config.flow_aggr_sums:
						r[common.getProtoFromValue(row[common.COL_PROTO])][s] += row[s]
	
				result[row[key[0]]] = r

		# no that we have calculated the indexes, take the values and postprocess them
		results = result.values()
		if sort:
			# TODO: implement sort function that allows for sorting with two keys
			if len(sort) != 1:
				raise HTTPError(output = "Cannot sort by multiple fields. This must yet be implemented.")
			if sort[0][1] == pymongo.ASCENDING:
				results.sort(key=operator.itemgetter(sort[0][0]))
			else:
				results.sort(key=operator.itemgetter(sort[0][0]), reverse=True)
		
		if limit:
			results = results[0:limit]
	
		return (total, reults)
		
	
	def find_one(self, collectionName, spec, fields, sort):
		collection = self.dst_db[collectionName]
		return collection.find_one(spec, fields=fields, sort=sort)



class MysqlBackend(Backend):
	def __init__(self, host, port, user, password, databaseName):
		import MySQLdb
		Backend.__init__(self, host, port, user, password, databaseName)
		self.tableInsertCache = dict()
		self.cachingThreshold = 10000
		self.counter = 0

		self.doCache = True

	def connect(self):
		import MySQLdb
		import _mysql_exceptions
		try:
			dns = dict(
				db = self.databaseName,
				host = self.host,
				port = self.port,
				user = self.user,
				passwd = self.password
			)         
			self.conn = MySQLdb.connect(**dns)
			self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
		except Exception as inst:
			print >> sys.stderr, "Cannot connect to MySQL database: ", inst 
			sys.exit(1)


	def execute(self, string):
		import MySQLdb
		import _mysql_exceptions
		
		try: 
			self.cursor.execute(string)
		except (AttributeError, MySQLdb.OperationalError):
			self.connect()
			self.execute(string)

	def executemany(self, string, objects):
		import MySQLdb
		import _mysql_exceptions
		try:
			self.cursor.executemany(string, objects)
		except (AttributeError, MySQLdb.OperationalError):
			self.connect()
			self.executemany(strin, objects)

	
	def clearDatabase(self):
		self.execute("SHOW TABLES")	
		tables = self.cursor.fetchall()
		for table in tables:
			self.execute("DROP TABLE " + table.values()[0])

	def prepareCollections(self):
		# we need to create several tables that contain flows and
		# pre aggregated flows, as well as tables for indexes that 
		# are precalculated on the complete data set. 

		# tables for storing bucketized flow data
		for s in config.flow_bucket_sizes:
			createString = "CREATE TABLE IF NOT EXISTS "
			createString += common.DB_FLOW_PREFIX + str(s) + " (_id VARBINARY(120) NOT NULL, bucket INTEGER(10) UNSIGNED NOT NULL"
			for v in config.flow_aggr_values:
				createString += ", %s %s NOT NULL" % (v, common.MYSQL_TYPE_MAPPER[v])
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.MYSQL_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])
			createString += ", PRIMARY KEY(_id))"
			self.execute(createString)

		# tables for storing aggregated timebased data
		for s in config.flow_bucket_sizes:
			createString = "CREATE TABLE IF NOT EXISTS "
			createString += common.DB_FLOW_AGGR_PREFIX + str(s) + " (_id VARBINARY(120) NOT NULL, bucket INTEGER(10) UNSIGNED NOT NULL"
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.MYSQL_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])
			createString += ", PRIMARY KEY(_id))"
			self.execute(createString)
		
		# create precomputed index that describe the whole data set
		for table in [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]:
			createString = "CREATE TABLE IF NOT EXISTS %s (_id INTEGER(10) UNSIGNED NOT NULL" % table
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.MYSQL_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])
			for direction in [ "src", "dst" ]:
				for s in config.flow_aggr_sums + [ "flows" ]:
					createString += ", %s %s DEFAULT 0" % (direction + "_" + s, common.MYSQL_TYPE_MAPPER[s])
				for proto in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]: 
						createString += ", %s %s DEFAULT 0" % (direction + "_" + proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])

			createString += ", PRIMARY KEY(_id))"
			self.execute(createString)

		# create tables for storing incremental indexes
		for bucket_size in config.flow_bucket_sizes:
			for index in [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]:
				table = index + "_" + str(bucket_size)
				createString = "CREATE TABLE IF NOT EXISTS %s (_id INTEGER(10) UNSIGNED NOT NULL, bucket INTEGER(10) UNSIGNED NOT NULL" % table
				for s in config.flow_aggr_sums + [ "flows" ]:
					createString += ", %s %s DEFAULT 0" % (s, common.MYSQL_TYPE_MAPPER[s])
				for proto in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]: 
						createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])
				for direction in [ "src", "dst" ]:
					for s in config.flow_aggr_sums + [ "flows" ]:
						createString += ", %s %s DEFAULT 0" % (direction + "_" + s, common.MYSQL_TYPE_MAPPER[s])
					for proto in common.AVAILABLE_PROTOS:
						for s in config.flow_aggr_sums + [ "flows" ]: 
							createString += ", %s %s DEFAULT 0" % (direction + "_" + proto + "_" + s, common.MYSQL_TYPE_MAPPER[s])
	
				createString += ", PRIMARY KEY(_id, bucket))"
				self.execute(createString)


	def createIndex(self, tableName, fieldName):
		try:
			self.execute("CREATE INDEX %s on %s (%s)" % (fieldName, tableName, fieldName))
		except:
			# most common cause: index does already exists
			# TODO check for errors
			pass

		
	def update(self, collectionName, statement, document, insertIfNotExists):
		# special handling for the _id field
		typeString = "_id"
		value = str(statement["_id"])
		if self.doCache: 
			if value == "total":
				# special value 0 encodes the total field
				cacheLine = (0,)
			else:
				cacheLine = (value,)
			valueString = "%s"
		else:
			if value == "total":
				valueString = "0"
			else:
				valueString = str(value)

		#if not collectionName ==common.DB_INDEX_NODES and not collectionName == common.DB_INDEX_PORTS:
		#	print collectionName,  statement, document
		updateString = ""
		for part in [ "$set", "$inc" ]:
			if not part in document:
				continue
			for v in document[part]:
				if self.doCache:
					cacheLine = cacheLine + (document[part][v],)
					valueString += ",%s"
				else:
					valueString += "," + str(document[part][v])
				v = v.replace('.', '_')
				typeString += "," + v
				if part == "$inc":
					if updateString != "":
						updateString += ","
					updateString +=  v + "=" + v + "+VALUES(" + v + ")"

		queryString = "INSERT INTO " + collectionName + "(" + typeString + ") VALUES (" + valueString + ") ON DUPLICATE KEY UPDATE " + updateString

		if self.doCache:
			numElem = 1
			if collectionName in self.tableInsertCache:
				cache = self.tableInsertCache[collectionName][0]
				numElem = self.tableInsertCache[collectionName][1] + 1
				if queryString in cache:
					cache[queryString].append(cacheLine)
				else:
					cache[queryString] = [ cacheLine ]
			else:
				cache = dict()
				cache[queryString] = [ cacheLine ]
		
			self.tableInsertCache[collectionName] = (cache, numElem)

			self.counter += 1
			#if self.counter % 100000 == 0:
				#print "Total len:",  len(self.tableInsertCache)
				#for c in self.tableInsertCache:
					#print c, len(self.tableInsertCache[c][0]), self.tableInsertCache[c][1]
			
			if numElem > self.cachingThreshold:
				self.flushCache(collectionName)
		else:
			self.execute(queryString)

	def flushCache(self, collectionName=None):
		if collectionName:
			cache = self.tableInsertCache[collectionName][0]
			for queryString in cache:
				cacheLines = cache[queryString]
				self.executemany(queryString, cacheLines)
			del self.tableInsertCache[collectionName]
		else:
			# flush all collections
			while len( self.tableInsertCache) > 0:
				collection = self.tableInsertCache.keys()[0]
				self.flushCache(collection)

	def getMinBucket(self, bucketSize = None):
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		tableName = common.DB_FLOW_PREFIX + str(bucketSize)
		self.execute("SELECT MIN(bucket) as bucket FROM %s" % (tableName))
		return self.cursor.fetchall()[0]["bucket"]
		
	def getMaxBucket(self, bucketSize = None):
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		tableName = common.DB_FLOW_PREFIX + str(bucketSize)
		self.execute("SELECT MAX(bucket) as bucket FROM %s" % (tableName))
		return self.cursor.fetchall()[0]["bucket"]

	def getBucketSize(self, startTime, endTime, resolution):
		for i,s in enumerate(config.flow_bucket_sizes):
			if i == len(config.flow_bucket_sizes)-1:
				return s
				
			tableName = common.DB_FLOW_AGGR_PREFIX + str(s)
			queryString = "SELECT bucket FROM %s WHERE bucket >= %d AND bucket <= %d ORDER BY bucket ASC LIMIT 1" % (tableName, startTime, endTime)
			self.execute(queryString);
			tmp = self.cursor.fetchall()
			minBucket = None
			if len(tmp) > 0:
				minBucket = tmp[0]["bucket"]

			queryString = "SELECT bucket FROM %s WHERE bucket >= %d AND bucket <= %d ORDER BY bucket DESC LIMIT 1" % (tableName, startTime, endTime)
			self.execute(queryString);
			tmp = self.cursor.fetchall()
			maxBucket = None
			if len(tmp) > 0:
				maxBucket = tmp[0]["bucket"]
			
			if not minBucket or not maxBucket:
				return s
			
			numSlots = (maxBucket-minBucket) / s + 1
			if numSlots <= resolution:
				return s

	def bucket_query(self, collectionName,  spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		print "MySQL: Constructing query ... "
		(result, total) = self.sql_query(collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)
		print "MySQL: Returning data to app ..."
		return result

	def index_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		return self.sql_query(collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)

	def dynamic_index_query(self, name, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		if name == "nodes":
			tableName = common.DB_INDEX_NODES + "_" + str(bucketSize)
		elif name == "ports":
			tableName = common.DB_INDEX_PORTS + "_" + str(bucketSize)
		else:
			raise Exception("Unknown index specified")

		(results, total) =  self.sql_query(tableName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize, [ "_id"])
		return (results, total)

	def sql_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize, aggregate = None):
		fieldList = ""
		if fields != None: 
			for field in fields:
				if field in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]:
						if fieldList != "":
							fieldList += ","
						fieldList += field + "_" + s
				else:
					if fieldList != "":
						fieldList += ","
					fieldList += field
			if not "bucket" in fields:
				fieldList += ",bucket"
		elif aggregate != None:
			# aggregate all fields
			fieldList = ""
			for field in aggregate:
				if fieldList != "":
					fieldList = ","
				fieldList += field 
			for field in config.flow_aggr_sums + [ "flows" ]:
				fieldList += ",SUM(" + field + ") as " + field
				for p in common.AVAILABLE_PROTOS:
					fieldList += ",SUM(" + p + "_" + field + ") as " + p + "_" + field
		else:
			fieldList = "*"

		isWhere = False
		queryString = "SELECT %s FROM %s " % (fieldList, collectionName)
		if startBucket != None and startBucket > 0:
			isWhere = True
			queryString += "WHERE bucket >= %d " % (startBucket)
		if endBucket != None and endBucket < sys.maxint:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else: 
				queryString += "AND "
			queryString += "bucket <= %d " % (endBucket)

		firstIncludePort = True
		for port in includePorts:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstIncludePort: 
					queryString += "AND ("
					firstIncludePort = False
				else:
					queryString += "OR "
			queryString += "%s = %d OR %s = %d " % (common.COL_SRC_PORT, port, common.COL_DST_PORT, port)
		if not firstIncludePort:
			queryString += ") "

		firstExcludePort = True
		for port in excludePorts:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstExcludePort: 
					queryString += "AND ("
					firstExcludePort = False
				else:
					queryString += "OR "
			queryString += "%s != %d OR %s != %d " % (common.COL_SRC_PORT, port, common.COL_DST_PORT, port)
		if not firstExcludePort:
			queryString += ") "

		firstIncludeIP = True
		for ip in includeIPs:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstIncludeIP: 
					queryString += "AND ("
					firstIncludeIP = False
				else:
					queryString += "OR "
			queryString += "%s = %d OR %s = %d " % (common.COL_SRC_IP, ip, common.COL_DST_IP, ip)
		if not firstIncludeIP:
			queryString += ") "


		firstExcludeIP = True
		for ip in excludeIPs:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstExcludeIP: 
					queryString += "AND ("
					firstExcludeIP = False
				else:
					queryString += "OR "
			queryString += "%s != %d OR %s != %d " % (common.COL_SRC_IP, ip, common.COL_DST_IP, ip)
		if not firstExcludeIP:
			queryString += ") "

		if aggregate:
			queryString += "GROUP BY "
			firstField = True
			for field in aggregate:
				if not firstField:
					queryString += ","
				else:
					firstField = False
				queryString += field + " "

		if sort:
			queryString += "ORDER BY " + sort[0][0] + " "
			if sort[0][1] == 1:
				queryString += "ASC "
			else: 
				queryString += "DESC "

		if limit:
			queryString += "LIMIT %d" % (limit)

		print "MySQL: Running Query ..."
		self.execute(queryString)
		queryResult =  self.cursor.fetchall()
		print "MySQL: Encoding Query ..."
		result = []
		total = dict()

		# TODO: Performance. Mysql returns Decimals instead of standard ints when aggregating
		#       While this is not a problem in itself, ujson cannot encode this
		#       and the result cannot be transmitted to the browser. We therefore do conversions
		#       to int, which hurts performance. We should either do
		#       1.) use MySQLDb.converters.conversions and change the mapping dict
		#       2.) fix ujson
		# 	Instead we convert it while encoding ...

		for row in queryResult:
			resultDoc = dict()
			isTotal = False
			for field in row:
				if field == "_id":
					if row[field] == 0:
						isTotal = True
					fieldParts = []
				else: 
					fieldParts = field.split('_')
				if len(fieldParts) > 1:
					# maximum depth is 3 
					# TODO: hacky ... 
					if len(fieldParts) == 2:
						if not fieldParts[0] in resultDoc:
							resultDoc[fieldParts[0]] = dict()
						resultDoc[fieldParts[0]][fieldParts[1]] = int(row[field])
					elif len(fieldParts) == 3:
						# TODO: not implemented ... 
						pass
					else:
						raise Exception("Internal Programming Error!")
				else:
					if field == "_id":
						resultDoc["id"] = int(row[field])
					else: 
						resultDoc[field] = int(row[field])
			if isTotal:
				total = resultDoc
			else:
				result.append(resultDoc)

		print "Got Results: ", len(result)
		#print "Total: ", total
		#print "Result: ", result
		#for r in result: 
		#	print r
		return (result, total)

	def run_query(self, collectionName, query):
		finalQuery = query % (collectionName)
		self.execute(finalQuery)
		return self.cursor.fetchall()

class OracleBackend(Backend):
	def __init__(self, host, port, user, password, databaseName):
		Backend.__init__(self, host, port, user, password, databaseName)
		self.tableInsertCache = dict()
		self.cachingThreshold = 10000
		self.counter = 0

		self.doCache = True
		self.connect()

		self.tableNames = [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]
		for s in config.flow_bucket_sizes:
			self.tableNames.append(common.DB_FLOW_PREFIX + str(s))
			self.tableNames.append(common.DB_FLOW_AGGR_PREFIX + str(s))
			for index in [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]:
				self.tableNames.append(index + "_" + str(s))

	def connect(self):
		import cx_Oracle
		print "Oracle: Attempting new connect:" 
		try:
			connection_string = self.user + "/" + self.password + "@" + self.host + ":" + str(self.port) + "/" + self.databaseName
			print connection_string
			self.conn = cx_Oracle.Connection(connection_string)

			self.cursor = cx_Oracle.Cursor(self.conn)
		except Exception as inst:
			print >> sys.stderr, "Cannot connect to Oracle database: ", inst 
			sys.exit(1)


	def execute(self, string, params = None):
		import cx_Oracle
		try: 
			if params == None:
				self.cursor.execute(string)
			else:
				self.cursor.execute(string, params)
			self.conn.commit()
		except (AttributeError, cx_Oracle.OperationalError) as e:
			print e
			self.connect()
			self.execute(string)
		except cx_Oracle.DatabaseError as e:
			print e 
			error, = e.args
			if error.code == 955:
				print "Table already exists!"
			else:
				print e
				print "Have seen unknown error. Terminating!"
				sys.exit(-1)


	def executemany(self, string, objects):
		import cx_Oracle
		try:
			self.cursor.executemany(string, objects)
			self.conn.commit()
		except (AttributeError, cx_Oracle.OperationalError):
			self.connect()
			self.executemany(string, objects)

	def query(self, tablename, string):
		string = string % (tableName)
		self.execute(string)
		return self.cursor.fetchall()

	def insert(self, collectionName, fieldDict):
		queryString = "MERGE INTO " + collectionName + " target USING (SELECT "
		selectString = ""
		matchedString = ""
		notMatchedInsert = ""
		notMatchedValues = ""
		primary = ""
		params = {}
		for field in fieldDict:
			if selectString != "":
				selectString += ","
			if notMatchedInsert != "":
				notMatchedInsert += ","
			if notMatchedValues != "":
				notMatchedValues += ","
			selectString += ":"+field  + " as " + field
			params[field] = str(fieldDict[field][0])
			if fieldDict[field][1] == None:
				if matchedString != "":
					matchedString += ","
				matchedString += field + "=" + "SOURCE." + field + "+" + "target." + field
			notMatchedInsert += "target." + field
			notMatchedValues += "SOURCE." + field
			if fieldDict[field][1] != None:
				if primary != "":
					primary += " AND "
				primary += "target." + field + "=SOURCE." + field
		
		queryString += selectString + " FROM dual) SOURCE ON (" + primary + ")"
		queryString += "WHEN MATCHED THEN UPDATE SET " + matchedString
		queryString += " WHEN NOT MATCHED THEN INSERT (" + notMatchedInsert + ") VALUES (" + notMatchedValues + ")" 
		if self.doCache:
			numElem = 1
			if collectionName in self.tableInsertCache:
				cache = self.tableInsertCache[collectionName][0]
				numElem = self.tableInsertCache[collectionName][1] + 1
				if queryString in cache:
					cache[queryString].append(params)
				else:
					cache[queryString] = [ params ]
			else:
				cache = dict()
				cache[queryString] = [ params ]
		
			self.tableInsertCache[collectionName] = (cache, numElem)

			self.counter += 1
			#if self.counter % 100000 == 0:
				#print "Total len:",  len(self.tableInsertCache)
				#for c in self.tableInsertCache:
					#print c, len(self.tableInsertCache[c][0]), self.tableInsertCache[c][1]
			
			if numElem > self.cachingThreshold:
				self.flushCache(collectionName)
		else:
			self.execute(queryString, params)

	def clearDatabase(self):
		import cx_Oracle
		for table in self.tableNames:
			try:
				self.cursor.execute("DROP TABLE " + table)
			except cx_Oracle.DatabaseError as e:
				error, = e.args
				if error.code == 942:
					print "Table " + table + " does not exist"
			except Exception as e:
				print "Have seen unknown error:", e
				print "Terminating!"
				sys.exit(-1)

	def prepareCollections(self):
		# we need to create several tables that contain flows and
		# pre aggregated flows, as well as tables for indexes that 
		# are precalculated on the complete data set. 

		# tables for storing bucketized flow data
		for s in config.flow_bucket_sizes:
			primary = "bucket"
			createString = "CREATE TABLE "
			createString += common.DB_FLOW_PREFIX + str(s) + " (bucket NUMBER(10) NOT NULL"
			for v in config.flow_aggr_values:
				primary += "," + v
				createString += ", %s %s NOT NULL" % (v, common.ORACLE_TYPE_MAPPER[v])
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.ORACLE_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])
			createString += ", PRIMARY KEY(" + primary + "))"
			self.execute(createString)

		# tables for storing aggregated timebased data
		for s in config.flow_bucket_sizes:
			createString = "CREATE TABLE "
			createString += common.DB_FLOW_AGGR_PREFIX + str(s) + " (bucket NUMBER(10) NOT NULL"
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.ORACLE_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])
			createString += ", PRIMARY KEY(bucket))"
			self.execute(createString)
		
		# create precomputed index that describe the whole data set
		for table in [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]:
			createString = "CREATE TABLE %s (id NUMBER(10) NOT NULL" % table
			for s in config.flow_aggr_sums + [ "flows" ]:
				createString += ", %s %s DEFAULT 0" % (s, common.ORACLE_TYPE_MAPPER[s])
			for proto in common.AVAILABLE_PROTOS:
				for s in config.flow_aggr_sums + [ "flows" ]: 
					createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])
			for direction in [ "src", "dst" ]:
				for s in config.flow_aggr_sums + [ "flows" ]:
					createString += ", %s %s DEFAULT 0" % (direction + "_" + s, common.ORACLE_TYPE_MAPPER[s])
				for proto in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]: 
						createString += ", %s %s DEFAULT 0" % (direction + "_" + proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])

			createString += ", PRIMARY KEY(id))"
			self.execute(createString)

		# create tables for storing incremental indexes
		for bucket_size in config.flow_bucket_sizes:
			for index in [ common.DB_INDEX_NODES, common.DB_INDEX_PORTS ]:
				table = index + "_" + str(bucket_size)
				createString = "CREATE TABLE %s (id NUMBER(10) NOT NULL, bucket NUMBER(10) NOT NULL" % table
				for s in config.flow_aggr_sums + [ "flows" ]:
					createString += ", %s %s DEFAULT 0" % (s, common.ORACLE_TYPE_MAPPER[s])
				for proto in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]: 
						createString += ", %s %s DEFAULT 0" % (proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])
				for direction in [ "src", "dst" ]:
					for s in config.flow_aggr_sums + [ "flows" ]:
						createString += ", %s %s DEFAULT 0" % (direction + "_" + s, common.ORACLE_TYPE_MAPPER[s])
					for proto in common.AVAILABLE_PROTOS:
						for s in config.flow_aggr_sums + [ "flows" ]: 
							createString += ", %s %s DEFAULT 0" % (direction + "_" + proto + "_" + s, common.ORACLE_TYPE_MAPPER[s])
	
				createString += ", PRIMARY KEY(id, bucket))"
				self.execute(createString)


	def createIndex(self, tableName, fieldName):
		try:
			self.execute("CREATE INDEX %s on %s (%s)" % (fieldName, tableName, fieldName))
		except:
			# most common cause: index does already exists
			# TODO check for errors
			pass

		
	def update(self, collectionName, statement, document, insertIfNotExists):
		fieldDict = {}
		for s in statement:
			if collectionName.startswith("index"):
				# special handling for total field
				if statement[s] == "total":
					fieldDict["id"] = (0, "primary")
				else:
					fieldDict["id"] = (statement[s], "primary")

		for part in [ "$set", "$inc" ]:
			if not part in document:
				continue
			for v in document[part]:
				newV = v.replace('.', '_')
				if part == "$set":
					fieldDict[newV] = (document[part][v], "primary")
				else:
					fieldDict[newV] = (document[part][v], None)
		self.insert(collectionName, fieldDict)

	def flushCache(self, collectionName=None):
		if collectionName:
			cache = self.tableInsertCache[collectionName][0]
			for queryString in cache:
				cacheLines = cache[queryString]
				self.executemany(queryString, cacheLines)
			del self.tableInsertCache[collectionName]
		else:
			# flush all collections
			while len( self.tableInsertCache) > 0:
				collection = self.tableInsertCache.keys()[0]
				self.flushCache(collection)

	def getMinBucket(self, bucketSize = None):
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		tableName = common.DB_FLOW_PREFIX + str(bucketSize)
		self.execute("SELECT MIN(bucket) as bucket FROM %s" % (tableName))
		return self.cursor.fetchall()[0]["bucket"]
		
	def getMaxBucket(self, bucketSize = None):
		if not bucketSize:
			# use minimal bucket size
			bucketSize = config.flow_bucket_sizes[0]
		tableName = common.DB_FLOW_PREFIX + str(bucketSize)
		self.execute("SELECT MAX(bucket) as bucket FROM %s" % (tableName))
		return self.cursor.fetchall()[0]["bucket"]

	def getBucketSize(self, startTime, endTime, resolution):
		for i,s in enumerate(config.flow_bucket_sizes):
			if i == len(config.flow_bucket_sizes)-1:
				return s
				
			tableName = common.DB_FLOW_AGGR_PREFIX + str(s)
			queryString = "SELECT * FROM (SELECT bucket FROM %s WHERE bucket >= %d AND bucket <= %d ORDER BY bucket ASC) where ROWNUM <= 1" % (tableName, startTime, endTime)
			self.execute(queryString);
			tmp = self.cursor.fetchall()
			minBucket = None
			if len(tmp) > 0:
				minBucket = tmp[0][0]

			queryString = "SELECT * FROM (SELECT bucket FROM %s WHERE bucket >= %d AND bucket <= %d ORDER BY bucket DESC) WHERE ROWNUM <= 1" % (tableName, startTime, endTime)
			self.execute(queryString);
			tmp = self.cursor.fetchall()
			maxBucket = None
			if len(tmp) > 0:
				maxBucket = tmp[0][0]
			
			if not minBucket or not maxBucket:
				return s
			
			numSlots = (maxBucket-minBucket) / s + 1
			if numSlots <= resolution:
				return s

	def bucket_query(self, collectionName,  spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		print "Oracle: Constructing query ... "
		(result, total) = self.sql_query(collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)
		print "Oracle: Returning data to app ..."
		return result

	def index_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		return self.sql_query(collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize)

	def dynamic_index_query(self, name, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize):
		if name == "nodes":
			tableName = common.DB_INDEX_NODES + "_" + str(bucketSize)
		elif name == "ports":
			tableName = common.DB_INDEX_PORTS + "_" + str(bucketSize)
		else:
			raise Exception("Unknown index specified")

		(results, total) =  self.sql_query(tableName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize, [ "id"])
		return (results, total)

	def sql_query(self, collectionName, spec, fields, sort, limit, count, startBucket, endBucket, resolution, bucketSize, biflow, includePorts, excludePorts, includeIPs, excludeIPs, batchSize, aggregate = None):
		fieldList = ""
		if fields != None: 
			for field in fields:
				if field in common.AVAILABLE_PROTOS:
					for s in config.flow_aggr_sums + [ "flows" ]:
						if fieldList != "":
							fieldList += ","
						fieldList += field + "_" + s
				else:
					if fieldList != "":
						fieldList += ","
					fieldList += field
			if not "bucket" in fields:
				fieldList += ",bucket"
		elif aggregate != None:
			# aggregate all fields
			fieldList = ""
			for field in aggregate:
				if fieldList != "":
					fieldList = ","
				fieldList += field 
			for field in config.flow_aggr_sums + [ "flows" ]:
				fieldList += ",SUM(" + field + ") as " + field
				for p in common.AVAILABLE_PROTOS:
					fieldList += ",SUM(" + p + "_" + field + ") as " + p + "_" + field
		else:
			fieldList = "*"

		isWhere = False
		queryString = "SELECT %s FROM %s " % (fieldList, collectionName)
		if startBucket != None and startBucket > 0:
			isWhere = True
			queryString += "WHERE bucket >= %d " % (startBucket)
		if endBucket != None and endBucket < sys.maxint:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else: 
				queryString += "AND "
			queryString += "bucket <= %d " % (endBucket)

		firstIncludePort = True
		for port in includePorts:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstIncludePort: 
					queryString += "AND ("
					firstIncludePort = False
				else:
					queryString += "OR "
			queryString += "%s = %d OR %s = %d " % (common.COL_SRC_PORT, port, common.COL_DST_PORT, port)
		if not firstIncludePort:
			queryString += ") "

		firstExcludePort = True
		for port in excludePorts:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstExcludePort: 
					queryString += "AND ("
					firstExcludePort = False
				else:
					queryString += "OR "
			queryString += "%s != %d OR %s != %d " % (common.COL_SRC_PORT, port, common.COL_DST_PORT, port)
		if not firstExcludePort:
			queryString += ") "

		firstIncludeIP = True
		for ip in includeIPs:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstIncludeIP: 
					queryString += "AND ("
					firstIncludeIP = False
				else:
					queryString += "OR "
			queryString += "%s = %d OR %s = %d " % (common.COL_SRC_IP, ip, common.COL_DST_IP, ip)
		if not firstIncludeIP:
			queryString += ") "


		firstExcludeIP = True
		for ip in excludeIPs:
			if not isWhere:
				queryString += "WHERE " 
				isWhere = True
			else:
				if firstExcludeIP: 
					queryString += "AND ("
					firstExcludeIP = False
				else:
					queryString += "OR "
			queryString += "%s != %d OR %s != %d " % (common.COL_SRC_IP, ip, common.COL_DST_IP, ip)
		if not firstExcludeIP:
			queryString += ") "

		if aggregate:
			queryString += "GROUP BY "
			firstField = True
			for field in aggregate:
				if not firstField:
					queryString += ","
				else:
					firstField = False
				queryString += field + " "

		if sort:
			queryString += "ORDER BY " + sort[0][0] + " "
			if sort[0][1] == 1:
				queryString += "ASC "
			else: 
				queryString += "DESC "

		if limit:
			queryString = "SELECT * from (" + queryString + ") WHERE ROWNUM <=" + str(limit)

		print "Oracle: Running Query ..."
		self.execute(queryString)
		queryResult =  self.cursor.fetchall()
		print "Oracle: Encoding Query ..."
		result = []
		total = dict()

		columns = [i[0].lower() for i in self.cursor.description]
		#TODO: this is hacky ..
		if 'srcip' in columns:
			columns[columns.index('srcip')] = "srcIP"
		if 'dstip' in columns:
			columns[columns.index('dstip')] = "dstIP"

		for row in queryResult:
			resultDoc = dict()
			isTotal = False
			idx = 0
			for field in columns:
				fieldValue = row[idx]
				if field == "id":
					if fieldValue == 0:
						isTotal = True
					fieldParts = []
				else: 
					fieldParts = field.split('_')
				if len(fieldParts) > 1:
					# maximum depth is 3 
					# TODO: hacky ... 
					if len(fieldParts) == 2:
						if not fieldParts[0] in resultDoc:
							resultDoc[fieldParts[0]] = dict()
						resultDoc[fieldParts[0]][fieldParts[1]] = int(fieldValue)
					elif len(fieldParts) == 3:
						# TODO: not implemented ... 
						pass
					else:
						raise Exception("Internal Programming Error!")
				else:
					if field == "_id":
						resultDoc["id"] = int(fieldValue)
					else: 
						resultDoc[field] = int(fieldValue)
				idx += 1
			if isTotal:
				total = resultDoc
			else:
				result.append(resultDoc)

		print "Got Results: ", len(result)
		#print "Total: ", total
		#print "Result: ", result
		#for r in result: 
		#	print r
		return (result, total)

	def run_query(self, collectionName, query):
		finalQuery = query % (collectionName)
		self.execute(finalQuery)
		return self.cursor.fetchall()



def getBackendObject(backend, host, port, user, password, databaseName):
	if backend == "mongo":
		return MongoBackend(host, port, user, password, databaseName)
	elif backend == "mysql":
		return MysqlBackend(host, port, user, password, databaseName)
	elif backend == "oracle":
		return OracleBackend(host, port, user, password, databaseName)
	else:
		raise Exception("Backend " + backend + " is not a supported backend")
