#!/usr/bin/python
# Search for files within the specified term
# (Months or specific date)
# Returns a list of files matching the criteria
def sl_find_files(room, user, d, t=3):
	hgt_logger.debug('\t sl_find_files args : {} :: {}'.format(d, t))

	_dir = expanduser('~') + '/.purple/logs/jabber/'
	hgt_logger.debug('\t Pidgin log path : {}'.format(_dir))

	# Check if a date was passed
	if type(d) is datetime.date:
		hgt_logger.debug('\t Searching on date : {}'.format(d))
		exact_date = d

	# If not a date, process monthly term passed
	else:
		if t == '# of Months':
			t=3
		begin_date = monthdelta(datetime.date.today(), int(t))
		hgt_logger.debug('\t Searching for term : {}'.format(t))
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
	
	hgt_logger.debug('\t Added {!s} files to the list'.format(len(_files)))
	hgt_logger.debug('\t Sorting files...')					
	_files.sort(key=lambda x: os.path.getmtime(x))
	return _files

# Returns all lines matching the passed term
def sl_find_lines(keyword, user, _file):
	#hgt_logger.debug('\t sl_find_lines pid({})'.format(os.getpid()))
	
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
