#!/usr/bin/python
#************************System Functions*******************************
def sys_create_alias():
	bashrc_path = '{}.bashrc'.format(os.path.expanduser('~/'))
	bashrc_alias = "alias hgtools='nohup python {}/hgtools_gtk.py > /dev/null 2>&1 &'"
	
	with open(bashrc_path) as bashrc_file:
		found = False
		for line in bashrc_file:
			if bashrc_alias in line:
				found = True
				break
	
	if not found:
		hgt_logger.info('[*] Adding alias :')
		cmnd='echo "{}" >> {}'.format(bashrc_alias, bashrc_path)
		hgt_logger.debug('\t Command : {}'.format(cmnd))
		subprocess.call(cmnd, shell=True)	# Safe since input is curated
	else:
		hgt_logger.info('[*] Alias Found!')
		
# Logging
def setup_logger(name, level, file_loc):
	
	# Get the logger and set the level
	logger = logging.getLogger(name)
	logger.setLevel(level)
	
	# Create the formatters
	file_formatter = logging.Formatter('%(asctime)s %(levelname)s\t%(message)s', '%d-%m-%Y %H:%M:%S')
	cons_formatter = logging.StreamHandler('%(message)s')
	
	# Create the handlers
	file_handler = logging.FileHandler(file_loc, mode='a')
	file_handler.setFormatter(file_formatter)
	logger.addHandler(file_handler)
	
	last_run = logging.FileHandler(LAST_RUN_PATH, 'w')
	last_run.setFormatter(file_formatter)
	logger.addHandler(last_run)
	
	if level==logging.DEBUG:
		
		cons_handler = logging.StreamHandler(sys.stdout)
		cons_handler.setFormatter(cons_formatter)
		logger.addHandler(cons_handler)
	
	return logger
	
#************************AHK import function****************************
#	Path to autokey.json : ~/.config/autokey
# 
#	If user has custom script folders :
#	Location in file :
#	"folders": [
#       "CUSTOM"
#       "FOLDER"
#       "PATHS"
#    ]
#
#	Otherwise AHKs are in ~/.config/autokey/data

def iahk_import_ahk():
	
	hgt_logger.info('[*] Importing User AHKs')

	conf_path = '{}/.config/autokey/autokey.json'.format(expanduser('~'))
	ahk_paths = []
	read = False
	
	try:
		ahk_paths = iahk_read_paths(conf_path)
		ahk_paths = iahk_strip_dups(ahk_paths)
		file_list = iahk_file_list(ahk_paths)
		iahk_send_sql(file_list)
						
	except Exception as e:
		hgt_logger.error("[*] import_ahk error : {}".format(e))
		raise
		
def iahk_send_sql(file_list):
	hgt_logger.debug('\t Writing to DB...')
	for item in file_list:
		with open('{}/{}'.format(item[0], item[1])) as this_file:
			item[2] = this_file.read().replace('"', '\'')
			item[1].strip('.txt')
			hgt_logger.debug('\t {} written'.format(item[1]))
			str_sql = 'INSERT INTO hgtools (hgt_code, hgt_text, hgt_group, hgt_arg1, hgt_arg2) '
			str_sql += 'VALUES ("{}","{}", "{}", "{}", "{}");'.format(item[1].strip('.txt'), item[2], 'UPL', ENV_USER, item[0])
			
			retval = hgt_query(str_sql)
			if retval:
				hgt_logger.debug('\t retval : {}'.format(retval))
			this_file.close()
		
def iahk_read_paths(path):
	hgt_logger.debug('\t Locating AHK paths...')
	paths = []
	read = False
	# Read paths to autokey files
	with open(path) as j:
		paths.append('{}/.config/autokey/data'.format(expanduser('~')))
		for line in j.read().splitlines():
			if '"folders": [],' in line:
				break
			if (read and ']' in line):
				break
			elif read:
				paths.append(line.strip(',"'' ''\"\n'))
				hgt_logger.debug('\t Added {}'.format(line.strip(',"'' ''\"\n')))
			if '"folders": [' in line:
				read = True
	j.close()
	return paths

# Parse out duplicated paths
def iahk_strip_dups(paths):
	hgt_logger.debug('\t Removing duplicated (nested) paths')
	non_dups = []
	ignore = []
	for i in range(len(paths)):
		for item in paths:
			if paths[i] in item:
				if paths[i] != item:
					hgt_logger.debug('\t Skipped {}'.format(item))
					ignore.append(item)
				elif item not in ignore:
					hgt_logger.debug('\t Kept {}'.format(item))
					non_dups.append(item)
	return non_dups

# Add File Path and File Name to the outFile list
def iahk_file_list(paths):
	hgt_logger.debug('\t Locating AHK .txt files')
	olist = []
	for path in paths:
		hgt_logger.debug('\t Looking in {}'.format(path))
		for root, dirs, files in os.walk(path):
			for _file in files:
				if ".txt" in _file:
					hgt_logger.debug('\t Located {}'.format(_file))
					olist.append([os.path.join(root), _file, ''])
	return olist
	
def iahk_csv_export(opath):
	
	str_sql = 'SELECT hgt_idx, hgt_text, hgt_group, hgt_code, hgt_arg1, '
	str_sql += 'hgt_arg2 from hgtools'
	
	_data = hgt_query(str_sql)
	
	with open(opath, 'wb') as csvfile:
		o_writer = csv.writer(csvfile, delimiter=',',
							quotechar="'", quoting=csv.QUOTE_MINIMAL)
		o_writer.writerow(('Record ID', 'Predefine', 'Group', 'Title', 
							'User', 'Path'))
		for line in _data.splitlines():
			o_writer.writerow(str(line).split('\t'))
		
	csvfile.close()
	
#************************/AHK import function***************************

# Validates the argument format if date type
def valid_date(s):
	hgt_logger.debug('\t valid_date args : {}'.format(s))
	
	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		hgt_logger.error("[*] Not a valid date: '{}'.".format(s))
		ve_win = InfoDialog(None, "Invalid Date", "Not a valid date: '{}'.".format(s))
		response = ve_win.run()
		ve_win.destroy()
		
# Return path to a resource based on relative path passed
def hgt_resource_path(rel_path):
	dir_of_py_file = os.path.dirname(__file__)
	rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
	abs_path_to_resource = os.path.abspath(rel_path_to_resource)
	return abs_path_to_resource
	
class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)
