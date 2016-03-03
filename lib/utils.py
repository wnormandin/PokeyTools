#!/usr/bin/python
#************************Utility Functions******************************
from HTMLParser import HTMLParser
import os
import logging
import inspect

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

	pokeylogger.info('[*] Importing User AHKs')

	conf_path = '{}/.config/autokey/autokey.json'.format(expanduser('~'))
	ahk_paths = []
	read = False

	try:
		ahk_paths = iahk_read_paths(conf_path)
		ahk_paths = iahk_strip_dups(ahk_paths)
		file_list = iahk_file_list(ahk_paths)
		iahk_send_sql(file_list)

	except Exception as e:
		pokeylogger.error("[*] import_ahk error : {}".format(e))
		raise

def iahk_send_sql(file_list):
	pokeylogger.debug('\t Writing to DB...')
	for item in file_list:
		with open('{}/{}'.format(item[0], item[1])) as this_file:
			item[2] = this_file.read().replace('"', '\'')
			item[1].strip('.txt')
			pokeylogger.debug('\t {} written'.format(item[1]))
			str_sql = 'INSERT INTO hgtools (hgt_code, hgt_text, hgt_group, hgt_arg1, hgt_arg2) '
			str_sql += 'VALUES ("{}","{}", "{}", "{}", "{}");'.format(item[1].strip('.txt'), item[2], 'UPL', ENV_USER, item[0])

			retval = hgt_query(str_sql)
			if retval:
				pokeylogger.debug('\t retval : {}'.format(retval))
			this_file.close()

def iahk_read_paths(path):
	pokeylogger.debug('\t Locating AHK paths...')
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
				pokeylogger.debug('\t Added {}'.format(line.strip(',"'' ''\"\n')))
			if '"folders": [' in line:
				read = True
	j.close()
	return paths

# Parse out duplicated paths
def iahk_strip_dups(paths):
	pokeylogger.debug('\t Removing duplicated (nested) paths')
	non_dups = []
	ignore = []
	for i in range(len(paths)):
		for item in paths:
			if paths[i] in item:
				if paths[i] != item:
					pokeylogger.debug('\t Skipped {}'.format(item))
					ignore.append(item)
				elif item not in ignore:
					pokeylogger.debug('\t Kept {}'.format(item))
					non_dups.append(item)
	return non_dups

# Add File Path and File Name to the outFile list
def iahk_file_list(paths):
	pokeylogger.debug('\t Locating AHK .txt files')
	olist = []
	for path in paths:
		pokeylogger.debug('\t Looking in {}'.format(path))
		for root, dirs, files in os.walk(path):
			for _file in files:
				if ".txt" in _file:
					pokeylogger.debug('\t Located {}'.format(_file))
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

# Returns the path of the calling file
def get_path(f=inspect.stack()[-1][1]):
	return os.path.dirname(os.path.realpath(f))

# Runs post-exit script
def application_exit(base_path=get_path()):
	cmd = ['bash', '{}/{}'.format(base_path, "post.sh")]
	subprocess.Popen(cmd)
	sys.exit(0)

# Validates the argument format if date type
def valid_date(s):
	pokeylogger.debug('\t valid_date args : {}'.format(s))

	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		pokeylogger.error("[*] Not a valid date: '{}'.".format(s))
		ve_win = InfoDialog(None, "Invalid Date", "Not a valid date: '{}'.".format(s))
		response = ve_win.run()
		ve_win.destroy()

# Return absolute path to a resource
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
