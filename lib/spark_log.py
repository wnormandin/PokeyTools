#!/usr/bin/python

import sys, time, os, datetime, webbrowser, logging, argparse
from multiprocessing import Pool
from sllib import *
from log import *

MULTIPROC=True
MAX_PROC=5

def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="Specify a date - YYYY-MM-DD", 
						type=valid_date)
	parser.add_argument("-r", "--room", help="Specify a room (inet, support, etc)")
	parser.add_argument("-u", "--user", help="Specify a User by LDAP (ie. wnormandin)")
	parser.add_argument("-k", "--keyword", help="Specify a Search Term")
	parser.add_argument("-t", "--term",	help="Specify a range in months to search (default is 3 months)",
						type=int, default=3)
	parser.add_argument("-l", "--logging",	help="Turn on logging messages",
						action="store_true")
						
	args = parser.parse_args()
	
	spark_logger=log_init(LOG_PATH, args.logging)
	spark_logger.debug("Logger {} spawned!".format(sys.argv[0]))
	spark_logger.info('spark_log.py {}'.format(args))
	
	# Define Output Path
	fpath = './.parsed/'
	spark_logger.debug('Output path : {}'.format(fpath))

	# Populate search arguments
	str_search = {}
	for arg in vars(args):
		str_search[arg]=getattr(args, arg)
		spark_logger.debug('Argument captured :{}:{}'.format(arg, getattr(args, arg)))

	_lines = []
	_opath = ('{}/dev/.spark_log/.parsed.html'.format(expanduser('~')))

	# Display Splash and Parse Arguments
	lib_out(' ', 'LOGO')
	time.sleep(1)

	# Filter by Absolute Date or Term
	if str_search['date']!=None:
		_files = find_files(datetime.datetime.date(datetime.datetime.strptime(str_search['date'], '%Y-%m-%d')), str_search)
		spark_logger.debug("Searching on {}".format(str_search['date']))
	else:
		_term = 3 if str_search['term'] == None else str_search['term']
		_files = find_files(1, str_search, _term)
		spark_logger.debug("Searching the past {} months".format(str_search['term']))

	# Check for MULTIPROC and process accordingly
	spark_logger.debug('MULTIPROC = {}'.format(MULTIPROC))
	if not MULTIPROC:
		for _file in _files:
			_lines.append(sl_find_lines(str_search, _file))
			spark_logger.debug('File searched : {}'.format(_file))
	else:
		i = 0
		spark_logger.debug('Parent (this) process : {}'.format(os.getpid()))
		while i in range(len(_files)):
			j = len(_files)-i
			this_min = min(MAX_PROC, j)
			pool = Pool(processes=this_min)
			chunk = _files[i:i+this_min]
			results = [None for _ in range(this_min)]
			
			for k in range(this_min):
				results[k] = pool.apply_async(sl_find_lines, [str_search, chunk[k]])
				
			pool.close()
			pool.join()
			
			for k in range (this_min):
				_lines.extend(results[k].get())
				
			i += this_min
				
	spark_logger.debug('{} files searched'.format(len(_files)))
	spark_logger.debug('{} lines found'.format(len(_lines)))

	open(_opath, 'w').close() # Empty File Contents
	spark_logger.debug('{} reinitialized'.format(_opath))

	# Write new file data
	with open(_opath, 'w') as f:
		spark_logger.debug('Writing {} lines'.format(len(_lines)))
		
		for l in _lines:
			f.write(clean_line(l))

	webbrowser.open(_opath, new=2)	

if __name__ == '__main__':
	main()
