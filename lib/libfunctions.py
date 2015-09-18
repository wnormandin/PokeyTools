#!/usr/bin/python

import sys, getopt, datetime, time, os, logging
from os.path import expanduser
from log import *
spark_logger = logging.getLogger('spark_tools.py')

#******************************FUNCTIONS********************************

# Used for printing messages stored in the library files
def lib_out(e , msg):
	# If Passed "LOGO" displays the script header
	spark_logger.debug('lib_out args : {} :: {}'.format(e, msg))
	
	lib_s = '{}{}'.format(expanduser('~'), _PATH)

	print e
	with open(lib_s, 'r') as f:
		
		for num, line in enumerate(f, 1):
			spark_logger.debug('lib_out image located at {}'.format(num))
			if '<{}>'.format(msg) in line:
				break

		# Continue from the first instance
		for line in f:

			# Break on the second instance
			if '</{}>'.format(msg) in line:
				break

			# Otherwise print the line
			print line.strip("\r\n")

# Validates the argument format if date type
def valid_date(s):
	spark_logger.debug('valid_date args : {}'.format(s))
	
	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		spark_logger.error("Not a valid date: '{}'.".format(s))
		sys.exit(3)
        
# Strip excess characters
def clean_line(l):
	# spark_logger.debug('clean_line args : %s' % l)
	
	_l = str(l)
	remove = ['[[', ']]', '[', ']']
	_l.translate(None, ''.join(remove))
	return _l

# Search for files within the specified term
# (Months or specific date)
# Returns a list of files matching the criteria
def find_files(d, str_search, t=3):
	spark_logger.debug('find_files args : {} :: {}'.format(d, t))

	_dir = expanduser('~') + '/.purple/logs/jabber/'
	spark_logger.debug('Pidgin log path : {}'.format(_dir))

	# Check if a date was passed
	if type(d) is datetime.date:
		spark_logger.debug('Searching on date : {}'.format(d))
		exact_date = d

	# If not a date, process monthly term passed
	else:
		begin_date = monthdelta(datetime.date.today(), int(t))
		spark_logger.debug('Searching for term : {}'.format(d))
		exact_date = 1

	_files = []
	for dirpath, subdirs, files in os.walk(_dir, onerror=None):
		
		for f in files:
			_path = os.path.join(dirpath, f)
			
			if exact_date != 1:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) == exact_date:
					if filter_rooms(_path, str_search):
						spark_logger.debug('Adding {} to the list'.format(_path))
						_files.append(_path)
						
			else:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) > begin_date:
					if filter_rooms(_path, str_search):
						spark_logger.debug('Adding {} to the list'.format(_path))
						_files.append(_path)
	
	spark_logger.debug('Added {!s} files to the list'.format(len(_files)))
	spark_logger.debug('Sorting files...')					
	_files.sort(key=lambda x: os.path.getmtime(x))
	return _files

# Returns all lines matching the passed term
def find_lines(str_search, _file):
	spark_logger.debug('find_lines args : {} :: {}'.format(_file, str_search))
	
	_lines = []
	look_for = ('keyword', 'user')
	keys = [i for i in look_for if i in list(str_search.keys()) and str_search[i]!=None]
	spark_logger.debug('Keys found : {}'.format(keys))
	
	with open(_file, 'r') as f:
		for line in f:
			if keys:
				for key in keys:
					spark_logger.debug('Searching for : {}'.format(str_search[key]))
					if line.find(str_search[key])>0:
						_lines.append('<br>' + clean_line(f.name) + '<br>')
						for _line in f:
							_lines.append(_line.rstrip())
						break
			else:
				_lines.append(line.rstrip())
	
	spark_logger.debug('Added {0!s} lines to output'.format(len(_lines)))
	return _lines

# Filter paths for room or user as specified
def filter_rooms(_path, str_search):
	
	check_for = ('room', 'user')
	found = False
	
	for key in list(str_search.keys()):
		if key in check_for:
			if (str_search[key] != None and _path.find(str_search[key]) > 0):
				spark_logger.debug("Found {0} in {1}".format(str_search[key], _path))
				found = True
				
	return found
		
# Calculate the date to return
def monthdelta(date, delta):
	m, y = (date.month-delta) % 12, date.year + ((date.month)-delta-1) // 12
	if not m: m = 12
	d = 1
	return date.replace(day=d,month=m, year=y)

# Return path to resource based on relative path passed	
def get_resource_path(rel_path):
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource

