import analyzer
import csv_configurator
import math
import sys

from ordered_dict import OrderedDict

class ThresholdAnalyzer(analyzer.Analyzer):
	
	def __init__(self, name, parameters):
		
		# store state for individual 'instances'
		self.state = dict()
		self.name = name
	
		# constant parameters for all instances
		self.field = parameters['field']
		self.upper_limit = parameters['upper_limit']
		self.lower_limit = parameters['lower_limit']
		self.differential_mode = parameters['differential_mode']
#		self.overrun_protection = parameters['overrun_protection']

	# get new data set and pass it to individual instances
	def passDataSet(self, data):

		result = []
	
		# right now data contains only interface_phy
		# so actually main is router, and sub is interface
		for main in data:
			for sub in data[main]:
				try:
					tmp = self.analyzeDataSet(self.state[str(main) + "-" + str(sub)], data)
					if tmp != None:
						result.extend(tmp)
				except KeyError:
					self.state[str(main) + "-" + str(sub)] = {
						'mainid': main,
						'subid': sub,
						'last_value': None,
						'begin_low_exception': -1,
						'begin_high_exception': -1,
						'low_values': [],
						'high_values': []
					} 
					tmp = self.analyzeDataSet(self.state[str(main) + "-" + str(sub)], data)
					if tmp != None:
						result.extend(tmp)

		return result


	# analyze data for one instance
	# state - state for the analyzer, values that differ for each instance, i.e. last_value, st, ewmv
	def analyzeDataSet(self, state, data):
		timestamp = data[state['mainid']][state['subid']]["timestamp"]
		
		try:
			value = data[state['mainid']][state['subid']][self.field]

			if self.differential_mode:
				if state['last_value'] is None:
					state['last_value'] = data[state['mainid']][state['subid']][self.field]
					return
#				if value < state['last_value'] and self.overrun_protection:
#					print "!!!", value, state['last_value']
#					value = 2**32 + value
				value = value - state['last_value']
				state['last_value'] = data[state['mainid']][state['subid']][self.field]
	
		except KeyError:
			return ((self.name, state['mainid'], state['subid'], "KeyError", timestamp, timestamp, "%s not in data" % self.field, str(sys.exc_info())),)

		except TypeError:
			return ((self.name, state['mainid'], state['subid'], "TypeError", timestamp, timestamp, "%s not in data" % self.field, str(sys.exc_info())),)


		parameterdump = OrderedDict([
			("mainid", state['mainid']),
			("subid", state['subid']),
			("lower_limit", self.lower_limit),
			("upper_limit", self.upper_limit),
			("field", self.field),
			("value", value)
		])

		result = []

		# check for violation of lower_limit
		if self.lower_limit is not None and value > self.lower_limit:
			if state['begin_low_exception'] == -1:
				state['begin_low_exception'] = timestamp
				state['low_values'] = []
			state['low_values'] += [value]
			result.append((self.name, state['mainid'], state['subid'], "ValueException", state['begin_low_exception'], timestamp, "%s > %s" % (state['low_values'], self.lower_limit), str(parameterdump)))
		else:
			state['begin_low_exception'] = -1
	
		# check for violation of upper_limit
		if self.upper_limit is not None and value < self.upper_limit:
			if state['begin_high_exception'] == -1:
				state['begin_high_exception'] = timestamp
				state['high_values'] = []
			state['high_values'] += [value]
			result.append((self.name, state['mainid'], state['subid'], "ValueException", state['begin_high_exception'], timestamp, "%s < %s" % (state['high_values'], self.upper_limit), str(parameterdump)))
		else:
			state['begin_high_exception'] = -1

		return result

