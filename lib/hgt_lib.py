#!/usr/bin/python
from gi.repository import GObject, Pango
from gi.repository import Gtk, Gdk
import sys, getopt, datetime, time, os
import dbus, dbus.glib, dbus.decorators
import logging, getpass, webbrowser
from os.path import expanduser
from multiprocessing import Pool
from HTMLParser import HTMLParser
import re, csv, locale, random, inspect
import subprocess
import urllib2
import urllib
from subprocess import Popen, PIPE

#******************************GLOBALS**********************************

# Logging
# Default logging configuration settings
# https://docs.python.org/2/library/logging.html#logger-objects
LAST_RUN_PATH = './tmp/last_run.log'
hgt_logger = logging.getLogger('hgtools_gtk.py')

#Pass_Chats Functionality
PASS_LIST='./lib/pc_list.txt'
DOM_SUFFIX='@openfire.houston.hostgator.com'
PURPLE_CONV_TYPE_IM=1

# Spark_Log Functionality

MULTIPROC=True
MAX_PROC=2

# HGTools Functionality
USER_SELECTION=0

# GUI
ENV_USER = getpass.getuser()
CSS_PATH = './lib/hgt_win_style.css'
UI_INFO_PATH = './lib/ui_info.xml'

# User Administration
USER_LEVEL = 'USER'

#******************************/GLOBALS*********************************

#******************************FUNCTIONS********************************

# Logging
def setup_logger(name, level, file_loc):
	
	# Get the logger and set the level
	logger = logging.getLogger(name)
	logger.setLevel(level)
	
	# Create the formatters
	file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(module)s >> %(message)s')
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

#************************User Functions*********************************
# Functions to grant admin permissions to some users

def user_main(user=ENV_USER):
	
	if user_first_logon(user):
		hgt_logger.debug('[*] First user logon detected : {}'.format(user))
		user_db_add(user)
	msg = 'hgtools_gtk accessed'
	user_db_log(msg, user)
	hgt_logger.debug('\t User Permission Level : {}'.format(USER_LEVEL))
		
def user_first_logon(user):
	
	str_sql = 'SELECT user_level FROM hgtools_users '
	str_sql += 'WHERE user_ldap="{}"'.format(user)
	
	global USER_LEVEL
	
	result = hgt_query(str_sql)
	
	if result:
		USER_LEVEL = result
		return False
	else:
		USER_LEVEL = 'USER'
		return True
	
def user_db_add(user):
	str_sql = 'INSERT INTO hgtools_users (user_ldap, user_level, user_group) '
	str_sql += 'VALUES ("{}", "{}", "{}");'.format(user, 'USER', 'NEW_USERS')
	hgt_query(str_sql)
	hgt_logger.debug('[*] User {} added to hgtools_users'.format(user))
	
def user_db_log(msg, user):
	str_sql = 'INSERT INTO hgtools_log (log_type, log_text) '
	str_sql += 'VALUES ("{}", "{}");'.format(user, msg)
	hgt_query(str_sql) 
	hgt_logger.debug('[*] DB Log Record Created > hgtools_log')

#************************/User Functions********************************

#************************AHK import function****************************
#	Path to autokey.json : ~/.config/autokey
# 
#	Location in file :
#	"folders": [
#       "/home/wnormandin/dev/scripts/AHKs",
#        "/home/wnormandin/dev/scripts/AHKs/Scripts",
#        "/home/wnormandin/dev/scripts/AHKs/Tickets"
#    ]
#

def iahk_import_ahk():
	
	hgt_logger.debug('[*] Importing User AHKs')

	conf_path = '{}/.config/autokey/autokey.json'.format(expanduser('~'))
	ahk_paths = []
	read = False
	
	try:
		ahk_paths = iahk_read_paths(conf_path)
		ahk_paths = iahk_strip_dups(ahk_paths)
		file_list = iahk_file_list(ahk_paths)
		iahk_send_sql(file_list)
						
	except Exception as e:
		hgt_logger.error("[*] import_ahk error : {}".format(*e))
		raise
		
def iahk_send_sql(file_list):
	hgt_logger.debug('\t Writing to DB...')
	for item in file_list:
		with open('{}/{}'.format(item[0], item[1])) as this_file:
			item[2] = this_file.read().replace('"', '\'')
			item[1].strip('.txt')
			hgt_logger.debug('\t {} written'.format(item[1]))
			str_sql = 'INSERT INTO hgtools (hgt_code, hgt_text, hgt_group) '
			str_sql += 'VALUES ("{}","{}", "{}");'.format(item[2][:4].strip(' ').replace(' ', '_'), item[2], 'UPL')
			
			retval = hgt_query(str_sql)
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
	
#************************/AHK import function***************************
	
#************************hgfix functionality****************************
def hgfix_do_encode(post_arguments):

	# Encode It Properly
	uri = urllib.urlencode(post_arguments)
	uri = uri.encode('utf-8') # data should be bytes
	
	return urllib2.Request('http://hgfix.net/paste/api/create', uri)
	
def hgfix_do_post(request):

	# Make a POST Request
	response = urllib2.urlopen(request)
	
	# Read the Response
	paste_url = response.read().decode("utf-8").rstrip()  
	match = re.search(r"http://hgfix.net/paste/view/(.+)", paste_url)
	paste_url = "http://hgfix.net/paste/view/raw/" + match.group(1)
	
	return paste_url
	
def hgfix_do_paste(value, destination=False):
	
	if not destination:
		pass

	elif destination == 'clipboard':
		clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clip.set_text(value, -1)
		
	elif destination == 'mouse':
		p = Popen(['xsel', '-p'], stdin=PIPE)
		p.communicate(value)
		
def hgfix_main(txt, destination):

	hgfix_do_paste("Loading -- Try again in a moment")
	# Pair Up the URI Query String
	post_arguments = {'text' : txt, 'private': '', 'expires': '30', 'lang': 'text'}
	ret_url = hgfix_do_post(hgfix_do_encode(post_arguments))
	hgfix_do_paste(ret_url, destination)

#*********************spark_log functionality***************************

def sl_main(date, term, keyword, user, room):
	
	hgt_logger.debug('[*] Spark Log Search started')
	hgt_logger.debug('\t date : {} | term : {} | keyword : {} |'.format(date, term, keyword))
	hgt_logger.debug('\t user : {} | room : {} |'.format(user, room))
	
	# Define Output Path
	fpath = './.parsed/'
	hgt_logger.debug('\t Output path : {}'.format(fpath))

	_lines = []
	_opath = ('{}/dev/.spark_log/.parsed.html'.format(expanduser('~')))

	# Filter by Absolute Date or Term
	if date != 'Date':
		_files = sl_find_files(room, user, datetime.datetime.strptime(date, '%Y-%m-%d').date())
		hgt_logger.debug("\t Searching on {}".format(date))
	else:
		_files = sl_find_files(room, user, 1, term)
		hgt_logger.debug("\t Searching the past {} months".format(term))

	# Check for MULTIPROC and process accordingly
	hgt_logger.debug('\t MULTIPROC = {}'.format(MULTIPROC))
	if not MULTIPROC:
		for _file in _files:
			_lines.append(sl_find_lines(keyword, user, _file))
			hgt_logger.debug('\t File searched : {}'.format(os.path.basename(_file)))
	else:
		i = 0
		hgt_logger.debug('\t Parent (this) process : {}'.format(os.getpid()))
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
			
	hgt_logger.debug('\t {} files searched'.format(len(_files)))
	hgt_logger.debug('\t {} lines found'.format(len(_lines)))

	open(_opath, 'w').close() # Empty File Contents
	hgt_logger.debug('\t {} reinitialized'.format(_opath))
	
	if len(_lines) > 0:
		# Write new file data
		with open(_opath, 'w') as f:
			hgt_logger.debug('\t Writing {} lines'.format(len(_lines)))
			f.write('<!DOCTYPE html>')
			f.write('<html>')
			
			for l in _lines:
				if isinstance(l, (list, tuple)):
					for ln in l:
						f.write(ln)
				else:
					f.write(l)
		f.close()
		webbrowser.open(_opath, new=2)
		
	else:
		hgt_logger.info("[*] No Results Found")
		nr_win = InfoDialog(None, "No Results", "Query returned no results")
		response = nr_win.run()
		nr_win.destroy()

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

# Strip excess characters
def sl_clean_line(l):
	s = MLStripper()
	s.feed(str(l))
	
	cleaned = '{}<br>'.format(s.get_data())
	for ch in ['[', ']']:
		if ch in cleaned:
			cleaned = cleaned.replace(ch, '')
			
	return cleaned
	
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
	
	if len(_lines)>0:
		hgt_logger.debug('\t Added {} lines to output'.format(len(_lines)))
		
	return _lines

# Filter paths for room or user as specified
def sl_filter_rooms(_path, room, user):
	
	found = False
	
	if ((room=='Chat Room'or room==None) and (user=='User LDAP' or user==None)):
		found = True
	else:
		if (_path.find(user) > 0 ):
			hgt_logger.debug("\t Found {0} in {1}".format(user, os.path.basename(_path)))
			found = True
		if (_path.find(room) > 0):
			hgt_logger.debug("\t Found {0} in {1}".format(room, os.path.basename(_path)))
			found = True
			
	return found
		
# Calculate the date to return
def monthdelta(date, delta):
	m, y = (date.month-delta) % 12, date.year + ((date.month)-delta-1) // 12
	if not m: m = 12
	d = 1
	return date.replace(day=d,month=m, year=y)

# Return path to a resource based on relative path passed
def hgt_resource_path(rel_path):
	dir_of_py_file = os.path.dirname(__file__)
	rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
	abs_path_to_resource = os.path.abspath(rel_path_to_resource)
	return abs_path_to_resource
	
favicon = hgt_resource_path("./images/snappyfav.png")

#******************************PASS_CHATS*******************************
    
# Function to open the PassChats file 
def pc_addline(arg1, pl=PASS_LIST):

	hgt_logger.debug('[*] Opening {}'.format(pl))
	
	with open(pl, "a") as passlist:
		passlist.write("{}\n".format(arg1))
		hgt_logger.debug('\tAdded : {}'.format(arg1))
		
	passlist.close()
	hgt_logger.debug('\t{} closed'.format(pl))
	
# Function to open and return PassChats file contents
def pc_readlines(pl=PASS_LIST):

	hgt_logger.debug('[*] Opening {}'.format(pl))
	
	with open(PASS_LIST, "r") as passlist:
		hgt_logger.debug('\tReading lines...')
		lines = [line.strip() for line in passlist]
	hgt_logger.debug('\tRead {} lines'.format(len(lines)))	
	
	passlist.close()
	hgt_logger.debug('\t{} closed'.format(pl))
	
	return lines

# Pass Chats Request
def pc_pass_req(chats, lines):
	
	ex_flag=False

	hgt_logger.debug('[*] Testing dBus connection')

	bus = dbus.SessionBus()
	obj = bus.get_object("im.pidgin.purple.PurpleService", 
						"/im/pidgin/purple/PurpleObject")
	purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
	
	hgt_logger.debug('[*] Finding Pidgin Accounts')
	
	for acct in purple.PurpleAccountsGetAllActive():
		
		hgt_logger.debug('\tPidgin Acct : {!s}'.format(acct))
		
		for line in lines:
			
			hgt_logger.debug('\tFinding Pidgin Buddy : {}'.format(line))
			
			for buddy in purple.PurpleFindBuddies(acct, ''):
				
				if ex_flag:
					exit
				else:
					buddy_name = purple.PurpleBuddyGetName(buddy)
					
					if buddy_name==line+DOM_SUFFIX:
						
						hgt_logger.debug('\tBuddy Found!')
						hgt_logger.debug('[*] Attempting to message user :{}'.format(buddy_name))
							
						conv = purple.PurpleConversationNew(1, acct, buddy_name)
						im = purple.PurpleConvIm(conv)
						purple.PurpleConvImSend(im, pc_build_msg(str(chats)))
						
						hgt_logger.debug('\tMessage Sent to {}'.format(buddy_name))
						ex_flag=True			
	
def pc_build_msg(opt):
	msg = "\nCurrently I have : " + opt + " chats to pass.\nPlease reply if you can assist!\n"
	msg = msg + "\n\t[*] This has been an automated chat pass request."
	hgt_logger.debug('\tMessage :\t{}'.format(msg))
	return msg

def pc_do_test(dbg):
	
	buddy_count = 0
	acct_count = 0
	
	hgt_logger.debug('[*] Testing dBus connection')
	
	bus = dbus.SessionBus()
	
	try:
		obj = bus.get_object("im.pidgin.purple.PurpleService", 
							"/im/pidgin/purple/PurpleObject")
		purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
		
		hgt_logger.debug('\tSuccess...')
		hgt_logger.debug('[*] Checking for available Pidgin Buddies')
		
		for account in purple.PurpleAccountsGetAllActive():
			for buddy in purple.PurpleFindBuddies(account, ''):
				buddy_count += 1
			
			acct_count += 1
			
		hgt_logger.debug('\tSuccess...\n')

		hgt_logger.debug('\tLocated {!s} {}'.format(acct_count, 'Account(s)'))
		hgt_logger.debug('\tWith : {!s} {}'.format(buddy_count,'Buddies'))
		
	except Exception as e:
		if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
			nf_win = InfoDialog(self, "Error", 'Details : {:}'.format(*e))
			response = nf_win.run()
			nf_win.destroy()
		hgt_logger.error('[*] Details - {:}'.format(*e))
	
def pc_main(**kwargs):
	
	if kwargs is not None:
		
		# Build the list of buddies to send to	
		if 'list' in kwargs:
			lines = [line.strip() for line in open(PASS_LIST)]
			with open(PASS_LIST, "r") as passlist:
				lines = [line.strip() for line in passlist]
			passlist.close()
		
		# Add a specified buddy to the list	
		if 'buddy' in kwargs:
			for name, value in kwargs.items():
				if name=='buddy': lines.append(value)
		
		# Send the message to the list of buddies
		if ('buddy' in kwargs or 'list' in kwargs):
			for name, value in kwargs.items():
				if name=='chats': chat_count=value
			for name, value in kwargs.items():
				if name=='list': pc_pass_req(chat_count, lines)
		
#******************************/PASS_CHATS******************************

#********************************HGTOOLS********************************

#	Function takes str_sql, connects to the database, and returns 
#	the passed query results.
def hgt_query(str_sql, qtype=''):
	
	start = time.clock()
	user='wnrmndn_remote'
	password='^kb?i8kLByDL!'
	database='wnrmndn_hgtools'
	host='hgtools.normandindev.net'
	
	cmd=['mysql', '-h', host, '-u', user, '-p%s'%password, '-D', 
		database, '-Bse', str_sql]
		
	retval =subprocess.check_output(cmd)
	hgt_logger.debug('\t Database query took %s seconds' % (time.clock()-start))
	
	return retval
	
#	Function splits returned query output into a two-dimensional list
#	and passes it to the Gtk.window for user selection
def hgtools_buildlist(dinput, store):

	hgt_logger.debug('\t Populating Gtk.ListStore...')
	
	hgt_loadstore(dinput, store)	
	doutput=hgtools_getchoice(store)
	
	return doutput

#	Function imports the specified infile, then writes the records
#	to the hgtools database if possible
def hgt_imports(infile):
	
	hgt_logger.info('[*] Beginning import routine')

	row_count=0

	hgt_logger.info('\t Importing file : {}'.format(infile))
			
	with open(infile, 'rb') as csvfile:
		file_read = csv.reader(csvfile, delimiter=',', quotechar="'")
		
		rows = []
		for row in file_read:
			
			hgt_logger.debug(row)
			rows.append(row)
		
		validate_import(file_read, csvfile)
		
		dups = hgt_dedupe(rows).sort(reverse=True)
		
		# Delete the duplicates from the list to be uploaded
		hgt_logger.debug('Input Array Row Count : %s' % len(rows))
		for j in set(dups):
			hgt_logger.debug('\t Removed row in import : %s' % rows[int(j)])
			hgt_logger.debug('\t Import : %s - Input row %s' % (rows[int(j)], j))
			rows.remove(rows[int(j)])
					
		# Execute the append queries			
		for row in rows:
			hgt_logger.debug(str(row))
				
			hgt_query(hgt_qbuild('import', row), 'import')
			
			row_count += 1
	
	hgt_logger.info('\t Closing File...')
	csvfile.close()	

def validate_import(rows, csvfile):
	
	hgt_logger.info('\t Validating import format...')
	
	for row in rows:
		if (len(row)!=3 or row[0]==''):
			hgt_logger.error('\t **Check your file format : http://hgtools.normandindev.net/imports.php')
			csvfile.close()
			rows = []

#	Checks the list of records to be added and returns a list of
#	deduplicated values (chosen by the user)
def hgt_dedupe(rows):
	
	str_sql='SELECT DISTINCT hgt_text FROM hgtools ORDER BY hgt_idx ASC;'
	db_rec=trim_invalid(hgt_query(str_sql, 'dedupe'))
	rows = trim_invalid(rows[1])
	
	hgt_logger.info('[*] Running De-Duplication')
	hgt_logger.debug('\t Database records : {}'.format(len(db_rec)))
	hgt_logger.debug('\t Import records : {}'.format(len(rows)))
	hgt_logger.debug('\t Comparisons : {}'.format(len(db_rec)*len(rows)))
	
	dedupe_list, stats = dd_match(rows, db_rec, 0.0)
	
	hgt_logger.info('\t Dedupe Run Complete')
	hgt_logger.debug('\t Dedupe took {} seconds'.format(stats[2]))
	hgt_logger.debug('\t Dedupe List Length : {}'.format(len(dedupe_list)))
	hgt_logger.debug('\t Successful Comparisons : {}'.format(stats[0]))
	hgt_logger.debug('\t Potential Duplicates : {}'.format(stats[1]))
		
	store = Gtk.ListStore('gboolean', int, str, int, str, str, str)
	hgt_loadstore(dedupe_list, store)
	dups=hgtools_dd_choose(store, stats)
	
	hgt_logger.debug('\t Identified duplicates : {}'.format(len(dups)))
	return dups
	
def trim_invalid(rows):
	out_rows = []
	for row in rows:
		if len(row)>1:
			out_rows.append(row)
	return out_rows

def hgt_loadstore(dinput, store):
	
	for i in range(0, len(dinput)):
		try:
			store.append(dinput[i].split("\t"))
		except AttributeError:		
			store.append(list(dinput[i]))
		except ValueError:
			store.append(str(list(dinput[i])))

#********************************/HGTOOLS*******************************

#*********************************STYLE*********************************
def gtk_style():
	
	style_provider = Gtk.CssProvider()
	css = open(CSS_PATH, 'rb')
	css_data = css.read()
	css.close()
	style_provider.load_from_data(css_data)

	Gtk.StyleContext.add_provider_for_screen(
		Gdk.Screen.get_default(),
		style_provider,
		Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
def ui_xml():
	ui_info = open(UI_INFO_PATH, 'rb')
	ui_info_data = ui_info.read()
	ui_info.close
	return ui_info_data

#*********************************Classes*******************************

# Class to allow users to select from a list of potential matches, 
# matches with a score above the match_thresh will be auto-selected.
			
class DedupeSelectionWindow(Gtk.Window):
	
	def __init__(self, liststore, stats):
	
		Gtk.Window.__init__(self, title="HGTools Deduplication Window")
		hgt_logger.debug("HGTools Deduplication Window")
		hgt_logger.debug("Building grid")
		# Set Window/Grid attributes
		self.set_border_width(10)
		self.grid = Gtk.Grid()
		self.grid.set_column_homogeneous(True)
		self.grid.set_row_homogeneous(True)
		self.add(self.grid)
		self.selected=[]
		self.set_default_size(700, 400)
		self.connect("destroy", self.on_destroy)
		
		# Set the liststore of data for this object
		self.liststore = liststore
		self.treeview = Gtk.TreeView.new_with_model(self.liststore)
		
		hgt_logger.debug("Attaching columns")
		# Set Checkbox Column
		renderer_checkbox = Gtk.CellRendererToggle()
		renderer_checkbox.connect("toggled", self.on_toggle, self.liststore)
		
		# Create checkbox column and attach to element 0 in the
		# list store.
		column_checkbox = Gtk.TreeViewColumn("Match?", 
											renderer_checkbox, active=0)
		column_checkbox.set_sort_column_id(0)
		self.treeview.append_column(column_checkbox)
											
		# Set column headers
		for i, column_title in enumerate(["Import Row", "Import Text",
										"Match Row (DB)", "Matched Text",
										"Score", "Time(s)"]):
			renderer = Gtk.CellRendererText()
			renderer.props.wrap_width=400

			column = Gtk.TreeViewColumn(column_title, renderer, text=i+1)
			column.set_sort_column_id(i+1)
			self.treeview.append_column(column)
		
		# Fill Button list	
		self.buttons=list()
		for button_text in ["Cancel Import", "Done"]:
			button = Gtk.Button(button_text)
			self.buttons.append(button)
			button.connect("clicked", self.on_selection_button_clicked)
		
		self.scrollable_treelist = Gtk.ScrolledWindow()
		self.scrollable_treelist.set_vexpand(True)
		
		
		# Set up stat labels
		comparisons = Gtk.Label("Comparisons : " + stats[0] + '\t')
		potentials = Gtk.Label("Potential Matches : " + stats[1] + '\t')
		runtime = Gtk.Label("Test Run Time : " + stats[2])
		
		self.comparisons_label = comparisons
		self.potentials_label = potentials
		self.runtime_label = runtime
		
		# Attach treeview
		self.grid.attach(self.scrollable_treelist, 0, 1, 10, 10)
		self.grid.attach_next_to(self.buttons[0], self.scrollable_treelist, 
								Gtk.PositionType.BOTTOM, 1, 1)
		
		hgt_logger.debug("Attaching buttons")
		# Attach Buttons	
		for i, button in enumerate(self.buttons[1:]):
			self.grid.attach_next_to(button, self.buttons[i], 
								Gtk.PositionType.RIGHT, 1, 1)
								
		hgt_logger.debug("Attaching labels")						
		# Attach Labels
		self.grid.attach(self.comparisons_label, 0, 0, 1, 1)
		self.grid.attach_next_to(self.potentials_label, self.comparisons_label, 
								Gtk.PositionType.RIGHT, 1, 1)
		self.grid.attach_next_to(self.runtime_label, self.potentials_label, 
								Gtk.PositionType.RIGHT, 1, 1)
		
		# Check the boxes above the match threshold
		for i in range(len(liststore)):
			if liststore[i][0]==True:
				self.selected.append(liststore[i][3])
		
		hgt_logger.debug("Showing window")
		# Add the treelist in a scrollable window, center and show					
		self.scrollable_treelist.add(self.treeview)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.show_all()
	
	# Set button click events	
	def on_selection_button_clicked(self, widget):
		
		button_selection = widget.get_label()
		hgt_logger.debug("Button clicked : %s" % button_selection)
		
		if button_selection=="Cancel Import":
			while Gtk.events_pending():
				Gtk.main_iteration()
			Gtk.main_quit()
			sys.exit(3)
			
		if button_selection=="Done":
			Gtk.main_quit()
				
	def on_toggle(self, cell, path, model, *ignore):
		if path is not None:
			it = model.get_iter(path)
			model[it][0] = not model[it][0]
			
			if model[it][0]:
				if model[it][1] not in self.selected:
					self.selected.append(model[it][1])
					hgt_logger.debug("Selected : %s" % model[it][1])
			else:
				if model[it][1] in self.selected:
					self.selected.remove(model[it][1])
					hgt_logger.debug("Deselected : %s" % model[it][1])
			
	def delete_event(self, widget, event, data=None):
		hgt_logger.debug("Window deleted")
		Gtk.main_quit()
		
	def on_destroy(self, widget):
		hgt_logger.debug("Window destroyed")
		Gtk.main_quit()

class MLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)
		
class InfoDialog(Gtk.Dialog):
	
	global favicon

	def __init__(self, parent, ttl, msg):
		Gtk.Dialog.__init__(self, ttl, parent, 0,
			(Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(150, 100)
		self.set_icon_from_file(favicon)

		label = Gtk.Label(msg)

		box = self.get_content_area()
		box.add(label)
		self.show_all()

class SearchDialog(Gtk.Dialog):
	
	global favicon

	def __init__(self, parent):
		Gtk.Dialog.__init__(self, "Search", parent,
			Gtk.DialogFlags.MODAL, buttons=(
			Gtk.STOCK_FIND, Gtk.ResponseType.OK,
			Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

		self.set_icon_from_file(favicon)
		box = self.get_content_area()

		label = Gtk.Label("Search Term :")
		box.add(label)

		self.entry = Gtk.Entry()
		box.add(self.entry)

		self.show_all()


class LogViewWindow(Gtk.Window):
	
	global favicon
	
	def __init__(self):
		Gtk.Window.__init__(self, title=LAST_RUN_PATH)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_icon_from_file(favicon)

		self.set_default_size(800, 500)

		self.grid = Gtk.Grid()
		self.add(self.grid)

		self.create_textview()
		self.create_toolbar()

	def create_toolbar(self):
		toolbar = Gtk.Toolbar()
		self.grid.attach(toolbar, 0, 0, 3, 1)
		
		button_search = Gtk.ToolButton()
		icon_name = "system-search-symbolic"
		button_search.set_icon_name(icon_name)
		
		button_search.connect("clicked", self.on_search_clicked)
		toolbar.insert(button_search, 0)
		
	def create_textview(self):
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_hexpand(True)
		scrolledwindow.set_vexpand(True)
		self.grid.attach(scrolledwindow, 0, 1, 3, 1)
		
		self.textview = Gtk.TextView()
		self.textbuffer = self.textview.get_buffer()
		self.textbuffer.set_text(self.text_refresh())
		scrolledwindow.add(self.textview)
		
		self.tag_found = self.textbuffer.create_tag("found",
			background="yellow",
			weight=Pango.Weight.BOLD)
		
	def text_refresh(self):
		with open(LAST_RUN_PATH, 'r') as log_file:
			log_data = log_file.read()
		log_file.close
		return log_data
		
	def on_search_clicked(self, widget):
		dialog = SearchDialog(self)
		response = dialog.run()
		
		if response == Gtk.ResponseType.CANCEL:
			hgt_logger.debug("[*] SearchDialog > Cancel clicked")
			dialog.destroy()
			
		if response == Gtk.ResponseType.OK:
			hgt_logger.debug("[*] SearchDialog > Find clicked")
			cursor_mark = self.textbuffer.get_insert()
			start = self.textbuffer.get_iter_at_mark(cursor_mark)
			if start.get_offset() == self.textbuffer.get_char_count():
				start = self.textbuffer.get_start_iter()
			search_term = dialog.entry.get_text()
			hgt_logger.debug("\t Search term : {}".format(search_term))
			self.search_and_mark(search_term, start)
		dialog.destroy()

	def search_and_mark(self, text, start):
		end = self.textbuffer.get_end_iter()
		match = start.forward_search(text, 0, end)

		if match != None:
			match_start, match_end = match
			self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
			self.search_and_mark(text, match_end)

class MainWindow(Gtk.Window):
	
# Google Drive URL to diagram : https://drive.draw.io/#G0B6z1IIlV5HAPSWtrUTdjeW0tUU0

	global favicon
	global ENV_USER
	global MAX_PROC
	global MULTIPROC
	global USER_SELECTION
	
	def __init__(self):
		
		try:
			user_main()
			win_title = 'HG Tools | Welcome, {}!'.format(ENV_USER) 
			hgt_logger.setLevel(logging.DEBUG)
			# Create dict for signal storage
			self.selected = {}
			
			Gtk.Window.__init__(self, title=win_title)
			
			self.set_icon_from_file(favicon)
			self.pc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
			
			# Set CSS-Equivalent ID
			self.set_name("hgt_window")
			
			# Create Menu Action Group
			self.action_group = Gtk.ActionGroup("menu_actions")
			
			# Enumerate menu options
			self.add_file_menu_actions(self.action_group)
			self.add_data_menu_actions(self.action_group)
			self.add_option_menu_actions(self.action_group)
				
			# Create ui manager and attach actions
			uimanager = self.create_ui_manager()
			uimanager.insert_action_group(self.action_group)

			# Get menubar
			menubar = uimanager.get_widget("/MenuBar")
			
			# Widget Enumeration
			widgets = self.widget_config()
			
			# Grid/Box Constructor
			grid = Gtk.Grid()
			grid.set_border_width(1)
			grid.set_column_homogeneous(False)
			grid.set_row_homogeneous(False)
			grid.set_column_spacing(10)
			grid.set_row_spacing(10)
			self.box_config(menubar, grid, widgets)
			self.add(grid)

			self.set_position(Gtk.WindowPosition.CENTER)
			
			hgt_logger.debug("[*] HGTools GUI spawned")
			
		except Exception as e:
			raise
			#if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
			#	nf_win = InfoDialog(self, "Error", 'Details : {:}'.format(*e))
			#	response = nf_win.run()
			#	nf_win.destroy()
			#hgt_logger.error('[*] Details - {:}'.format(*e))
			
	# Actions
	
	def on_menu_file_csv_import(self, widget):
		hgt_logger.debug("[*] FileDialog Spawned!")
		dialog = Gtk.FileChooserDialog("Please choose a CSV file", self,
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		self.add_filters(dialog)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			hgt_logger.debug("\t FileDialog > Open clicked")
			hgt_logger.debug("\t File selected: {}".format(dialog.get_filename()))
		elif response == Gtk.ResponseType.CANCEL:
			hgt_logger.debug("\t FileDialog > Cancel clicked")

		dialog.destroy()

	def add_filters(self, dialog):
		filter_csv = Gtk.FileFilter()
		filter_csv.set_name("CSV files")
		filter_csv.add_mime_type("text/csv")
		dialog.add_filter(filter_csv)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)

	def add_file_menu_actions(self, action_group):
		action_filemenu = Gtk.Action("FileMenu", " File |", None, None)
		action_group.add_action(action_filemenu)

		action_filenewmenu = Gtk.Action("FileNew", None, None, Gtk.STOCK_NEW)
		action_group.add_action(action_filenewmenu)

		action_new = Gtk.Action("FileNewStandard", "_New (CSV) Import",
			"New (CSV) Import", Gtk.STOCK_NEW)
		action_new.connect("activate", self.on_menu_file_csv_import)
		action_group.add_action_with_accel(action_new, None)

		action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
		action_filequit.connect("activate", self.on_menu_file_quit)
		action_group.add_action(action_filequit)

	def add_data_menu_actions(self, action_group):
		action_group.add_actions([
			("DataMenu", None, " Data |"),
			("DataDeduplicate", None, "Deduplicate", None, None,
				self.on_menu_deduplicate),
			("CloneAHKLib", None, "Add AHK library to database", None, None,
				self.on_clone_ahks)
		])
		
	def add_option_menu_actions(self, action_group):
		action_group.add_actions([
			("OptionMenu", None, " Options |"),
			("MaxProcs", None, "Max Procs >"), ])
		action_group.add_toggle_actions([
			("DebugMode", None, "Debug Logging", None, 
			"Turn on/off verbose logging", self.on_debugmode, True),
			("MultiProc", None, "Multiprocessing", None, 
			"Turn on/off multiprocessing", self.on_multiproc, True), ])
		action_group.add_radio_actions([
			("Choice3", None, "3 Max", None, None, 1),
			("Choice4", None, "4 Max", None, None, 2),
			("Choice5", None, "5 Max", None, None, 3)
			], 1, self.on_maxprocs_changed)

	def on_debugmode(self, widget):
		hgt_logger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))
		if widget.get_active():
			hgt_logger.setLevel(logging.DEBUG)
			hgt_logger.debug("\t Debug Logging ON")
		else:
			hgt_logger.debug("\t Debug Logging OFF")
			hgt_logger.setLevel(logging.WARNING)
			
	def on_clone_ahks(self, menuitem):
		hgt_logger.debug('[*] Cloning user autokeys')
		
		# Prompt with mass upload warning
		nf_win = InfoDialog(self, "Notice", 'Notice, this will involve the mass upload of a large amount of data.')
		response = nf_win.run()
		nf_win.destroy()
		if response == Gtk.ResponseType.OK:
			iahk_import_ahk()
			
	def on_maxprocs_changed(self, widget, current):
		hgt_logger.debug("\t Max procs changed to : {}".format(current.get_name()[-1]))
		global MAX_PROC
		global MAX_PROC
		MAX_PROC = int(current.get_name()[-1])
			
	def on_multiproc(self, widget):
		hgt_logger.debug("\t Multiprocessing set to : {}".format(widget.get_active()))
		global MULTIPROC
		MULTIPROC = widget.get_active()

	def on_menu_deduplicate(self, widget):
		hgt_logger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))
	
	def create_ui_manager(self):
		uimanager = Gtk.UIManager()
		try:
			# Throws exception if something went wrong
			uimanager.add_ui_from_string(ui_xml())

			# Add the accelerator group to the toplevel window
			accelgroup = uimanager.get_accel_group()
			self.add_accel_group(accelgroup)
			return uimanager
			
		except Exception as e:
			if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
				nf_win = InfoDialog(self, "Error", 'Details : {:}'.format(*e))
				response = nf_win.run()
				nf_win.destroy()
				raise
			hgt_logger.error('[*] Details - {:}'.format(*e))

	def on_menu_file_quit(self, widget):
		hgt_logger.debug("[*] File > Quit Selected")
		Gtk.main_quit()

	def on_menu_others(self, widget):
		hgt_logger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))

	def on_menu_choices_changed(self, widget, current):
		hgt_logger.debug("[*] {} {}".format(current.get_name(), " was selected."))

	def on_menu_choices_toggled(self, widget):
		if widget.get_active():
			hgt_logger.debug("[*] {} {}".format(widget.get_name(), " activated"))
		else:
			hgt_logger.debug("[*] {} {}".format(widget.get_name(), " deactivated"))
			
	# Signal Events

	def pc_button_exec(self, widget):
		# Execute pass_chats
		hgt_logger.debug("[*] MainWindow > Broadcast button clicked")
		if self.selected['chats']!='# of Chats':
			pc_main(list=True, chats=self.selected['chats'])
		else:
			nf_win = InfoDialog(self, "Error", 'Select a chat count')
			response = nf_win.run()
			nf_win.destroy()

	def sl_button_exec(self, widget):
		# Execute spark_logs
		hgt_logger.debug("[*] MainWindow > Log Search button clicked")
		
		if self.sl_user_box.get_text():
			self.selected['user']=self.sl_user_box.get_text()
			
		if self.sl_keyword_box.get_text():
			self.selected['keyword']=self.sl_keyword_box.get_text()
			
		if self.sl_date_box.get_text():
			self.selected['date']=self.sl_date_box.get_text()
			
		if 'term' in self.selected:
			if self.selected['term']=='# of Months':
				self.selected['term']='3'
		if 'user' not in self.selected:
			self.selected['user']='User LDAP'
		if 'room' not in self.selected:
			self.selected['room']='Chat Room'
		if 'date' not in self.selected:
			self.selected['date']='Date'
		if 'keyword' not in self.selected:
			self.selected['keyword']='Keyword(s)'
			
		keys_to_select = ('user', 'room', 'date', 'keyword', 'term')
		sl_vars = dict((k, self.selected[k]) for k in keys_to_select)			
		sl_main(**sl_vars)
		
			# Arguments : (key - default - description)
	#
	#			date 	- None 	- Specific date (supercedes term)
	#			term 	- 3 	- Search depth in months
	#			room 	- None	- Search a specific chat room
	#			user 	- None 	- Search for a specific user
	#			keyword	- None	- Search for a keyword
		
	def sl_chatroom_combo_changed(self, combo):
		# Chatroom Combo Changed
		hgt_logger.debug("[*] MainWindow > Chatroom combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			hgt_logger.debug("\t Selected Chatroom = {}".format(name))
		self.selected['room']=name

	def menu_cl_button_exec(self, widget):
		# Close the window
		hgt_logger.debug("[*] MainWindow > Close button clicked")
		Gtk.main_quit()
		
	def menu_log_button_exec(self, widget):
		# Show the last_run log file
		hgt_logger.debug("[*] log_button clicked")
		log_win = LogViewWindow()
		log_win.connect("delete-event", Gtk.main_quit)
		hgt_logger.debug('[*] Showing LogViewWindow')
		log_win.show_all()
		hgt_logger.debug('[*] Entering Gtk.main()')
		Gtk.main()
		
	def pc_add_button_exec(self, widget):
		# Add a user to the pass_chats list
		hgt_logger.debug("[*] add_button clicked")
		
		if self.pc_ldap_box.get_text():
			self.selected['pc_ldap_box'] = self.pc_ldap_box.get_text()
		else:
			self.selected['pc_ldap_box'] = ''
			
		user_ldap = self.selected['pc_ldap_box']
		pc_addline(user_ldap)
		self.pc_ldap_box.set_text('Added!')
		self.pc_ldap_box.set_text('User LDAP')
		self.pc_list_refresh(widget)
		
		
	def pc_remove_button_exec(self, widget):
		# Remove a user from the pass_chats list
		hgt_logger.debug("[*] remove_button clicked")
		
		if 'user_selected' in self.selected:
			slctn = self.selected['user_selected']
			lines = pc_readlines()
			with open(PASS_LIST, "w") as passlist:
				for idx, val in enumerate(lines):
					if val!=slctn:
						passlist.write(val + "\n")
			passlist.close()
			self.pc_list_refresh(widget)
		else:
			hgt_logger.debug("\t No user specified!")
			nf_win = InfoDialog(self, "No user specified", "Please specify a user to remove!")
			response = nf_win.run()
			nf_win.destroy()
		
	def pc_chats_combo_changed(self, combo):
		# Chat count combo changed
		hgt_logger.debug("[*] MainWindow > Chat Count combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			hgt_logger.debug("\t Selected Chat Count = {}".format(name))
		self.selected['chats']=name
		
	def sl_depth_combo_changed(self, combo):
		# Search depth combo changed
		hgt_logger.debug("[*] MainWindow > Month Count combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			hgt_logger.debug("\t Selected Term  = {} months".format(name))
			self.selected['term']=name
		
	def pc_chatlist_selection_changed(self, selection):
		# pc_chatlist_treeview changed
		model, treeiter = selection.get_selected()
		if treeiter != None:
			sel = model[treeiter][0]
			hgt_logger.debug("[*] MainWindow > Your List > Selection changed to {}".format(sel))
			self.selected['user_selected']=sel

	# Window Format

	def box_config(self, menubar, grid, widgets):
		hgt_logger.debug('[*] Configuring Boxes')
		
		hgt_top_grid = Gtk.Grid()

		self.pc_widgets =  [widget for widget in widgets if '{!s}'.format(widget[0]).startswith('pc_')]
		hgt_logger.debug('\t len(pc_widgets) : {}'.format(len(self.pc_widgets)))
		self.pc_box_build(self.pc_box, self.pc_widgets)
		self.pc_box.set_homogeneous(False)

		sl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		sl_widgets =  [widget for widget in widgets if widget[0].startswith('sl_')]
		hgt_logger.debug('\t len(sl_widgets) : {}'.format(len(sl_widgets)))
		self.sl_box_build(sl_box, sl_widgets)
		sl_box.set_homogeneous(False)

		hgt_top_grid.add(self.pc_box)
		hgt_top_grid.attach_next_to(sl_box, self.pc_box, Gtk.PositionType.RIGHT, 1, 1)
		hgt_top_grid.set_column_homogeneous(True)
		hgt_top_grid.set_row_homogeneous(False)
		hgt_top_grid.set_column_spacing(10)
		hgt_top_grid.set_row_spacing(25)
		grid.add(menubar)
		grid.attach_next_to(hgt_top_grid, menubar, Gtk.PositionType.BOTTOM, 1, 2)

		self.hgt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		hgt_widgets = [widget for widget in widgets if widget[0].startswith('hgt_')]
		hgt_logger.debug('\t len(hgt_widgets) : {}'.format(len(hgt_widgets)))
		self.hgt_box_build(self.hgt_box, hgt_widgets)
		grid.attach_next_to(self.hgt_box, hgt_top_grid, Gtk.PositionType.BOTTOM, 1, 2)
		self.hgt_box.set_homogeneous(False)
		
		self.hgt_opt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		self.hgt_opt_box_build(self.hgt_opt_box)
		self.hgt_opt_box.set_homogeneous(False)
		grid.attach_next_to(self.hgt_opt_box, self.hgt_box, Gtk.PositionType.BOTTOM, 1, 2)
		
		self.hgt_opt2_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		self.hgt_opt2_box_build(self.hgt_opt2_box)
		self.hgt_opt2_box.set_homogeneous(False)
		grid.attach_next_to(self.hgt_opt2_box, self.hgt_opt_box, Gtk.PositionType.BOTTOM, 1, 2)
		
		menu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		menu_widgets = [widget for widget in widgets if widget[0].startswith('menu_')]
		hgt_logger.debug('\t len(menu_widgets) : {}'.format(len(menu_widgets)))
		self.menu_box_build(menu_box, menu_widgets)
		grid.attach_next_to(menu_box, self.hgt_opt2_box, Gtk.PositionType.BOTTOM, 1, 2)
		menu_box.set_homogeneous(False)
		
	def on_hgt_restype_toggled(self, radio, name):
		
		if radio.get_active():
			hgt_logger.debug('\t {}'.format(name))
			self.selected['hgt_rtype']=name
		
	def on_hgt_dest_toggled(self, radio, name):
		
		if radio.get_active():
			hgt_logger.debug('\t {}'.format(name))
			self.selected['hgt_dest']=name
		
	def pc_box_build(self, pc_box, pc_widgets):
		hgt_logger.debug('\t pc_box_build')
		
		# pc_label
		self.pc_label = Gtk.Label()
		self.pc_label.set_label(pc_widgets[0][1])
		self.pc_label.show()
		
		# pc_chats_combo
		self.pc_chats_combo_store = Gtk.ListStore(str)
		for item in pc_widgets[1][1]:
			self.pc_chats_combo_store.append(['{!s}'.format(item)])	
		self.pc_chats_combo = Gtk.ComboBox.new_with_model(self.pc_chats_combo_store)
		self.pc_chats_combo.set_tooltip_text(pc_widgets[1][2])
		self.pc_chats_combo.connect(*pc_widgets[1][3])
		self.renderer_text = Gtk.CellRendererText()
		self.pc_chats_combo.pack_start(self.renderer_text, True)
		self.pc_chats_combo.add_attribute(self.renderer_text, "text", 0)
		self.pc_chats_combo.set_active(0)
		
		# pc_chatlist_store
		self.pc_chatlist_store = Gtk.ListStore(str)
		for item in pc_widgets[2][1]:
			self.pc_chatlist_store.append([item])
		self.pc_chatlist_treeview = Gtk.TreeView(self.pc_chatlist_store)
		self.renderer = Gtk.CellRendererText()
		self.column = Gtk.TreeViewColumn("Your List", self.renderer, text=0)
		self.column.set_sort_column_id(0)
		self.pc_chatlist_treeview.append_column(self.column)
		self.select = self.pc_chatlist_treeview.get_selection()
		self.select.connect("changed", self.pc_chatlist_selection_changed)
		
		# pc_remove_button
		self.pc_remove_button = Gtk.Button.new_with_label(pc_widgets[3][1])
		self.pc_remove_button.set_tooltip_text(pc_widgets[3][2])
		self.pc_remove_button.connect(*pc_widgets[3][3])
		
		# pc_ldap_box
		self.pc_ldap_box = Gtk.Entry()
		self.pc_ldap_box.set_text(pc_widgets[4][1])
		self.pc_ldap_box.set_tooltip_text(pc_widgets[4][2])
		
		# pc_add_button
		self.pc_add_button =  Gtk.Button.new_with_label(pc_widgets[5][1])
		self.pc_add_button.set_tooltip_text(pc_widgets[5][2])
		self.pc_add_button.connect(*pc_widgets[5][3])
		
		# pc_subbox
		self.pc_subbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		self.pc_subbox.pack_start(self.pc_ldap_box, True, True, 1)
		self.pc_subbox.pack_start(self.pc_add_button, True, True, 1)
		
		# pc_button
		self.pc_button =  Gtk.Button.new_with_label(pc_widgets[6][1])
		self.pc_button.set_tooltip_text(pc_widgets[6][2])
		self.pc_button.connect(*pc_widgets[6][3])
		
		self.pc_box.pack_start(self.pc_label, True, True, 1)
		self.pc_box.pack_start(self.pc_chats_combo, True, True, 1)
		self.pc_box.pack_start(self.pc_chatlist_treeview, True, True, 1)
		self.pc_box.pack_start(self.pc_remove_button, True, True, 1)
		self.pc_box.pack_start(self.pc_subbox, True, True, 1)
		self.pc_box.pack_start(self.pc_button, True, True, 1)
		
	def pc_list_refresh(self, widget):
		store = Gtk.ListStore(str)
		for item in pc_readlines():
			store.append([item])
		self.pc_chatlist_treeview.set_model(store)
		
	def sl_box_build(self, sl_box, sl_widgets):
		hgt_logger.debug('\tsl_box_build')
		
		# sl_label
		self.sl_label = Gtk.Label()
		self.sl_label.set_label(sl_widgets[0][1])
		
		# sl_depth_combo
		self.sl_depth_combo_store = Gtk.ListStore(str)
		for item in sl_widgets[1][1]:
			self.sl_depth_combo_store.append(['{!s}'.format(item)])
		self.sl_depth_combo = Gtk.ComboBox.new_with_model(self.sl_depth_combo_store)
		self.sl_depth_combo.set_tooltip_text(sl_widgets[1][2])
		self.sl_depth_combo.connect(*sl_widgets[1][3])
		self.sl_depth_combo.set_entry_text_column(0)
		self.renderer_text = Gtk.CellRendererText()
		self.sl_depth_combo.pack_start(self.renderer_text, True)
		self.sl_depth_combo.add_attribute(self.renderer_text, "text", 0)
		self.sl_depth_combo.set_active(0)
		
		# sl_date_box
		self.sl_date_box = Gtk.Entry()
		self.sl_date_box.set_text(sl_widgets[2][1])
		self.sl_date_box.set_tooltip_text(sl_widgets[2][2])
		
		# sl_keyword_box
		self.sl_keyword_box = Gtk.Entry()
		self.sl_keyword_box.set_text(sl_widgets[3][1])
		self.sl_keyword_box.set_tooltip_text(sl_widgets[3][2])
		
		# sl_chatroom_combo
		self.sl_chatroom_combo_store = Gtk.ListStore(str)
		for item in sl_widgets[4][1]:
			self.sl_chatroom_combo_store.append([item])	
		self.sl_chatroom_combo = Gtk.ComboBox.new_with_model(self.sl_chatroom_combo_store)
		self.sl_chatroom_combo.set_tooltip_text(sl_widgets[4][2])
		self.sl_chatroom_combo.connect(*sl_widgets[4][3])
		self.renderer_text = Gtk.CellRendererText()
		self.sl_chatroom_combo.pack_start(self.renderer_text, True)
		self.sl_chatroom_combo.add_attribute(self.renderer_text, "text", 0)
		self.sl_chatroom_combo.set_active(0)
		
		# sl_user_box
		self.sl_user_box = Gtk.Entry()
		self.sl_user_box.set_text(sl_widgets[5][1])
		self.sl_user_box.set_tooltip_text(sl_widgets[5][2])
		
		# sl_button
		self.sl_button =  Gtk.Button.new_with_label(sl_widgets[6][1])
		self.sl_button.set_tooltip_text(sl_widgets[6][2])
		self.sl_button.connect(*sl_widgets[6][3])
		
		sl_box.pack_start(self.sl_label, True, True, 1)
		sl_box.pack_start(self.sl_depth_combo, True, True, 1)
		sl_box.pack_start(self.sl_date_box, True, True, 1)
		sl_box.pack_start(self.sl_keyword_box, True, True, 1)
		sl_box.pack_start(self.sl_chatroom_combo, True, True, 1)
		sl_box.pack_start(self.sl_user_box, True, True, 1)
		sl_box.pack_start(self.sl_button, True, True, 1)
		
	def hgt_opt_box_build(self, hgt_opt_box):
		hgt_logger.debug('\t hgt_opt_box')
		
		# hgt_opt_label
		hgt_opt_label = Gtk.Label()
		hgt_opt_label.set_label('Send Result to :')
		
		# hgt_dest_radio
		hgt_dest_radio1 = Gtk.RadioButton.new_with_label_from_widget(None, "XSel(Mouse)")
		hgt_dest_radio1.connect("toggled", self.on_hgt_dest_toggled, "1")
		hgt_dest_radio2 = Gtk.RadioButton.new_from_widget(hgt_dest_radio1)
		hgt_dest_radio2.set_label("Clipboard")
		hgt_dest_radio2.connect("toggled", self.on_hgt_dest_toggled, "2")
		hgt_dest_radio2.set_active(True)
		
		hgt_opt_box.pack_start(hgt_opt_label, False, False, 0)
		hgt_opt_box.pack_start(hgt_dest_radio1, False, False, 0)
		hgt_opt_box.pack_start(hgt_dest_radio2, False, False, 0)
		
	def hgt_opt2_box_build(self, hgt_opt2_box):
		hgt_logger.debug('\t hgt_opt_box')
		
		# hgt_opt_label
		hgt_opt_label = Gtk.Label()
		hgt_opt_label.set_label('Paste result as :')
		
		# hgt_dest_radio
		hgt_dest_radio1 = Gtk.RadioButton.new_with_label_from_widget(None, "Text")
		hgt_dest_radio1.connect("toggled", self.on_hgt_dest_toggled, "1")
		hgt_dest_radio2 = Gtk.RadioButton.new_from_widget(hgt_dest_radio1)
		hgt_dest_radio2.set_label("HGFix URL")
		hgt_dest_radio2.connect("toggled", self.on_hgt_restype_toggled, "2")
		hgt_dest_radio2.set_active(True)
		
		hgt_opt2_box.pack_start(hgt_opt_label, False, False, 0)
		hgt_opt2_box.pack_start(hgt_dest_radio1, False, False, 0)
		hgt_opt2_box.pack_start(hgt_dest_radio2, False, False, 0)
		
	def hgt_box_build(self, hgt_box, hgt_widgets):
		hgt_logger.debug('\t hgt_box_build')
		
		# hgt_search_box
		self.hgt_search_box = Gtk.Entry()
		self.hgt_search_box.set_text(hgt_widgets[0][1])
		self.hgt_search_box.set_tooltip_text(hgt_widgets[0][2])
		
		# hgt_button
		hgt_button =  Gtk.Button.new_with_label(hgt_widgets[1][1])
		hgt_button.set_tooltip_text(hgt_widgets[1][2])
		hgt_button.connect(*hgt_widgets[1][3])
		
		hgt_box.pack_start(self.hgt_search_box, True, True, 0)
		hgt_box.pack_start(hgt_button, False, False, 0)
		
	def menu_box_build(self, menu_box, menu_widgets):
		hgt_logger.debug('\t menu_box_build')
		
		# menu_cl_button
		menu_cl_button =  Gtk.Button.new_with_label(menu_widgets[0][1])
		menu_cl_button.set_tooltip_text(menu_widgets[0][2])
		menu_cl_button.connect(*menu_widgets[0][3])
		
		# menu_log_button
		menu_log_button =  Gtk.Button.new_with_label(menu_widgets[1][1])
		menu_log_button.set_tooltip_text(menu_widgets[1][2])
		menu_log_button.connect(*menu_widgets[1][3])
		
		menu_box.pack_start(menu_cl_button, True, True, 1)
		menu_box.pack_start(menu_log_button, True, True, 1)
		
	def widget_config(self):
		hgt_logger.debug('[*] Configuring Widgets')
		
		# Button 	=	(name, label, tooltip, signal)
		# Combo	Box	=	(name, values (default 1st), tooltip, signal)
		# Label		=	(name, label)
		# TreeView	=	(name, ListStore Values, tooltip)
		# Entry Box	=	(name, default, tooltip)
		
		hgt_widget=[]
		self.pc_section_widgets(hgt_widget)
		self.sl_section_widgets(hgt_widget)
		self.hgt_section_widgets(hgt_widget)
		self.menu_section_widgets(hgt_widget)
		return hgt_widget
	
	def pc_section_widgets(self, hgt_widget):
		hgt_logger.debug('\tpc_section_widgets')
		# Pass Chats Section
		# pc_label (Section title label)
		hgt_widget.append(('pc_label', 'Pass Chats'))
		
		# pc_chats_combo widget (Combo Box)
		pc_chats_combo_values = []
		pc_chats_combo_values.append('# of Chats')
		pc_chats_combo_values.extend(range(6))
		
		hgt_widget.append(('pc_chats_combo', pc_chats_combo_values,
							'The number of chats your\npass_chat message will show',
							["changed", self.pc_chats_combo_changed]))
							
		# pc_chatlist_treeview (Selectable TreeView list)
		hgt_widget.append(('pc_chatlist_treeview', 
							[line for line in pc_readlines()],
							'Your list of agents to broadcast\nrequests to'))
							
		# pc_remove_button widget (Action Button)
		hgt_widget.append(('pc_remove_button', 'Remove User',
							'Removes a user from your pass_chats list',
							["clicked", self.pc_remove_button_exec]))
							
		# pc_ldap_box widget (Entry Box)
		hgt_widget.append(('pc_ldap_box', 'User LDAP',
							"Enter a user's LDAP username\nto add to your pass_chat list"))
							
		# pc_add_button widget (Action Button)
		hgt_widget.append(('pc_add_button', 'Add',
							'Adds a user to your pass_chats list', 
							["clicked", self.pc_add_button_exec]))
		
		# pc_button widget (Action Button)
		hgt_widget.append(('pc_button', 'Broadcast',
							'Broadcasts a pass_chat message to\nthe users in your list',
							['clicked', self.pc_button_exec]))
							
	def sl_section_widgets(self, hgt_widget):
		hgt_logger.debug('\tsl_section_widgets')
		
		# Log Search Section
		# sl_label (Section title label)
		hgt_widget.append(('sl_label', 'Spark Log Search'))
		
		# sl_depth_combo (Combo Box)
		sl_depth_combo_values = []
		sl_depth_combo_values.append('# of Months')
		sl_depth_combo_values.extend(range(1, 12))
		
		hgt_widget.append(('sl_depth_combo', 
							sl_depth_combo_values,
							'Specify a search term in months (Max 12)', 
							["changed", self.sl_depth_combo_changed]))
							
		# sl_date_box (Entry Box)
		hgt_widget.append(('sl_date_box', 'Date',
							'Specify a date to search'))
							
		# sl_keyword_box (Entry Box)
		hgt_widget.append(('sl_keyword_box', 'Keyword(s)',
							'Specify keyword(s) to search'))
							
		# sl_chatroom_combo (Combo Box)
		hgt_widget.append(('sl_chatroom_combo', 
							['Chat Room', 'support', 'jdi', 'sales'], 
							'Specify a chat room to search', 
							["changed", self.sl_chatroom_combo_changed]))
							
		# sl_user_box (Entry Box)
		hgt_widget.append(('sl_user_box', 'User LDAP',
							'Specify user to search'))
							
		# sl_button widget (Action Button)
		hgt_widget.append(('sl_button', 'Search',
							'Search your Spark Logs with the\nspecified parameters',
							["clicked", self.sl_button_exec]))
		
	def hgt_section_widgets(self, hgt_widget):
		hgt_logger.debug('\thgt_section_widgets')
		
		# HGTools Search Section
		# hgt_search_box (Entry Box)
		hgt_widget.append(('hgt_search_box', 'Search Term', 
							'Specify a search term'))
							
		# hgt_button (Action Button)
		hgt_widget.append(('hgt_button', 'Predefine Search',
							'Searches for HGTools with text matching\nthe search term',
							["clicked", self.hgt_button_exec]))

	def menu_section_widgets(self, hgt_widget):
		hgt_logger.debug('\tmenu_section_widgets')
		
		# Menu Section
		# menu_cl_button (Action Button)
		hgt_widget.append(('menu_cl_button', 'Close Window',
							'Closes this window',
							["clicked", self.menu_cl_button_exec]))

		# menu_log_button (Action Button)
		hgt_widget.append(('menu_log_button', 'View Logs', 
							'Displays the file last_run.log', 
							["clicked", self.menu_log_button_exec]))
		
		return hgt_widget
		
	def hgt_button_exec(self, widget):
	# Execute hgtools search
		hgt_logger.debug("[*] MainWindow > Phrase Search clicked")
		
		if self.hgt_search_box.get_text():
			search_term=self.hgt_search_box.get_text()
			hgt_logger.debug("\t Search Term : {}".format(search_term))
			str_sql = 'SELECT hgt_code, hgt_text, hgt_desc FROM hgtools '
			str_sql += 'LEFT JOIN hgtools_codes ON hgt_code = hgtools_codes.code '
			str_sql += 'WHERE (hgt_text like "%{}%" OR hgt_code like "%{}%") GROUP BY hgt_code;'.format(search_term, search_term)
			outp=hgt_query(str_sql, 'phrases')
			
			# hgt_logger.debug("\t {}".format(outp))
			store = Gtk.ListStore(str, str, str)
			
			for line in outp.split('\n'):
				listed = line.split('\t')
				if listed != ['']:
					# hgt_logger.debug(listed)
					store.append(listed)
				
			if len(store)>0:
				search_win = SearchResultDialog(self, store)
				response = search_win.run()
				if response == Gtk.ResponseType.OK:
					hgt_logger.debug("\t Selected : {}".format(USER_SELECTION))
					search_win.destroy()
					try:
						if self.selected['hgt_dest'] == '2':
							dest = 'clipboard'
						else:
							dest = 'mouse'
							
						if self.selected['hgt_rtype'] == '1':
							src = 'Text'
							hgfix_do_paste(USER_SELECTION, dest)
						else:
							src = 'HGFix URL'
							hgfix_main(USER_SELECTION, dest)
							
						hgt_logger.debug("\t Response : {} - {} > {}".format(src, USER_SELECTION, dest))
						
					except Exception as e:
						raise
				else:
					hgt_logger.debug("\t User Cancelled Dialog")
					search_win.destroy()
					
			else:
				hgt_logger.debug("\t Term not found!")
				nf_win = InfoDialog(self, "Not Found", "No results for the specified search term!")
				response = nf_win.run()
				nf_win.destroy()
			
		else:
			hgt_logger.debug("\t No Term Specified")
			nf_win = InfoDialog(self, "No Term Specified", "Please enter a valid search term")
			response = nf_win.run()
			nf_win.destroy()
			
class SearchResultDialog(Gtk.Dialog):
	
	global USER_SELECTION
	
	def __init__(self, parent, store):
		Gtk.Dialog.__init__(self, "Select a record", parent, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
			 
		tree = Gtk.TreeView(store)
		renderer = Gtk.CellRendererText()
		renderer.props.wrap_width = 500
		scrollable_treelist = Gtk.ScrolledWindow()
		scrollable_treelist.set_vexpand(True)
		scrollable_treelist.set_hexpand(True)
		scrollable_treelist.set_border_width(10)
		scrollable_treelist.add(tree)
		
		self.set_border_width(1)
		self.set_size_request(1000, 300)

		col1 = Gtk.TreeViewColumn('Abbreviation', renderer, text=0) 
		
		col2 = Gtk.TreeViewColumn('Text', renderer, text=1)
		col2.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
		
		col3 = Gtk.TreeViewColumn('Description', renderer, text=2)
			
		for item in [col1, col2, col3]:
			tree.append_column(item)
			
		select = tree.get_selection()
		select.connect("changed", self.search_selection_changed)
		
		box = self.get_content_area()

		box.add(scrollable_treelist)
		self.show_all()
		
	def search_selection_changed(self, selection):
		global USER_SELECTION
		model, treeiter = selection.get_selected()
		if treeiter != None:
			USER_SELECTION = model[treeiter][1]
			hgt_logger.debug("\t Search window selection changed : {}".format(model[treeiter][0]))
		
