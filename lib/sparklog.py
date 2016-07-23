#!/usr/bin/python
# Search for files within the specified term
# (Months or specific date)
# Returns a list of files matching the criteria
import logging
import datetime
import os
from os.path import expanduser
from multiprocessing import Pool
from utils import MLStripper

pokeylogger = logging.getLogger('pokeylogger')

MULTIPROC=True
MAX_PROC=2

def sl_main(date, term, keyword, user, room):
	
	pokeylogger.info('[*] Spark Log Search started')
	pokeylogger.debug('\t date : {} | term : {} | keyword : {} |'.format(date, term, keyword))
	pokeylogger.debug('\t user : {} | room : {} |'.format(user, room))
	
	# Define Output Path
	fpath = './.parsed/'
	pokeylogger.debug('\t Output path : {}'.format(fpath))

	_lines = []
	_opath = ('{}/dev/.spark_log/.parsed.html'.format(expanduser('~')))

	# Filter by Absolute Date or Term
	if date != 'Date':
		_files = sl_find_files(room, user, datetime.datetime.strptime(date, '%Y-%m-%d').date())
		pokeylogger.debug("\t Searching on {}".format(date))
	else:
		_files = sl_find_files(room, user, 1, term)
		pokeylogger.debug("\t Searching the past {} months".format(term))

	# Check for MULTIPROC and process accordingly
	pokeylogger.debug('\t MULTIPROC = {}'.format(MULTIPROC))
	if not MULTIPROC:
		for _file in _files:
			_lines.append(sl_find_lines(keyword, user, _file))
			pokeylogger.debug('\t File searched : {}'.format(os.path.basename(_file)))
	else:
		i = 0
		pokeylogger.debug('\t Parent (this) process : {}'.format(os.getpid()))
		while i in range(len(_files)):
			j = len(_files)-i
			this_min = min(MAX_PROC, j)
			pool = Pool(processes=this_min)
			chunk = _files[i:i+this_min]
			results = [None for _ in range(this_min)]
		
			for k in range(this_min):
				results[k] = pool.apply_async(sl_find_lines, [keyword, user, chunk[k]])
				
			pool.close()
			pool.join()
			
			for k in range (this_min):
				_lines.extend(results[k].get())
				
			i += this_min
			
	pokeylogger.debug('\t {} files searched'.format(len(_files)))
	pokeylogger.debug('\t {} lines found'.format(len(_lines)))

	open(_opath, 'w').close() # Empty File Contents
	pokeylogger.debug('\t {} reinitialized'.format(_opath))
	
def sl_find_files(room, user, d, t=3):
	pokeylogger.debug('\t sl_find_files args : {} :: {}'.format(d, t))

	_dir = expanduser('~') + '/.purple/logs/jabber/'
	pokeylogger.debug('\t Pidgin log path : {}'.format(_dir))

	# Check if a date was passed
	if type(d) is datetime.date:
		pokeylogger.debug('\t Searching on date : {}'.format(d))
		exact_date = d

	# If not a date, process monthly term passed
	else:
		if t == '# of Months':
			t=3
		begin_date = monthdelta(datetime.date.today(), int(t))
		pokeylogger.debug('\t Searching for term : {}'.format(t))
		exact_date = 1

	_files = []
	for dirpath, subdirs, files in os.walk(_dir, onerror=None):
		
		for f in files:
			_path = os.path.join(dirpath, f)
			
			if exact_date != 1:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) == exact_date:
					if sl_filter_rooms(_path, room, user):
						_files.append(_path)	
			else:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) > begin_date:
					if sl_filter_rooms(_path, room, user):
						_files.append(_path)
	
	pokeylogger.debug('\t Added {!s} files to the list'.format(len(_files)))
	pokeylogger.debug('\t Sorting files...')					
	_files.sort(key=lambda x: os.path.getmtime(x))
	return _files

# Returns all lines matching the passed term
def sl_find_lines(keyword, user, _file):
	#pokeylogger.debug('\t sl_find_lines pid({})'.format(os.getpid()))
	
	_lines = []
	
	with open(_file, 'r') as f:
		for line in f:
			if (line.find(keyword)>0 or line.find(user)>0):
				_lines.append('<br><b><font color="blue">{}</font></b><br>'.format(sl_clean_line(f.name)))
				for _line in f:
					if isinstance(_line, (list, tuple)):
						for l in _line:
							lines.append('<br>{}'.format(sl_clean_line(l)))
					else:
						_lines.append('<br>{}'.format(sl_clean_line(_line.rstrip())))
				break
	f.close()
		
	return _lines

# Filter paths for room or user as specified
def sl_filter_rooms(_path, room, user):
	found = False
	if ((room=='Chat Room'or room==None) and (user=='User LDAP' or user==None)):
		found = True
	else:
		if (_path.find(user) > 0 or _path.find(room) > 0):
			found = True
	return found

# Strip excess characters
def sl_clean_line(l):
	s = MLStripper()
	s.feed(str(l))
	
	cleaned = '{}<br>'.format(s.get_data())
	for ch in ['[', ']']:
		if ch in cleaned:
			cleaned = cleaned.replace(ch, '')
			
	return cleaned
	
# Calculate the date to return (SL section)
def monthdelta(date, delta):
	m, y = (date.month-delta) % 12, date.year + ((date.month)-delta-1) // 12
	if not m: m = 12
	d = 1
	return date.replace(day=d,month=m, year=y)
