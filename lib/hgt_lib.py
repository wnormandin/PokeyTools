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
from urlparse import urlparse
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
USER_LEVEL = ''
VERS = 0.1

#******************************/GLOBALS*********************************

#******************************FUNCTIONS********************************

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

#************************User Functions*********************************
# Functions to grant admin permissions to some users

def user_main(user=ENV_USER):
	
	first_flag, u_lvl = user_first_logon(user)
	if first_flag:
		hgt_logger.info('[*] First user logon detected : {}'.format(user))
		user_db_add(user)
		sys_create_alias()
	msg = 'hgtools_gtk accessed'
	user_db_log(msg, user)
	hgt_logger.debug('\t User Permission Level : {}'.format(u_lvl))
	return u_lvl
		
def user_first_logon(user):
	
	str_sql = 'SELECT user_level FROM hgtools_users '
	str_sql += 'WHERE user_ldap="{}"'.format(user)
	result = hgt_query(str_sql)
	
	try:
		hgt_logger.debug('\t User found! Access : {}'.format(result.strip('\n')))
		return False, result.strip('\n')
	except:
		return True, 'USER'
	
def user_db_add(user):
	str_sql = 'INSERT INTO hgtools_users (user_ldap, user_level, user_group) '
	str_sql += 'VALUES ("{}", "{}", "{}");'.format(user, 'USER', 'NEW_USERS')
	hgt_query(str_sql)
	hgt_logger.info('[*] User {} added to hgtools_users'.format(user))
	
def user_db_log(msg, user):
	str_sql = 'INSERT INTO hgtools_log (log_type, log_text) '
	str_sql += 'VALUES ("{}", "{}");'.format(user, msg)
	hgt_query(str_sql) 
	hgt_logger.info('[*] DB Log Record Created > hgtools_log')

#************************/User Functions********************************

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
		
#**************************Domain Tools*********************************

def dmn_main():
	start=time.clock()
	clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
	url = clip.wait_for_text()
	print url
	
	flags = {}
	flags['url'] = url
	flags['urlparse'] = urlparse(url)
	flags['prop'] = ''
	flags['dns'] = ''
	
	dmn_parse(flags)
	
	if flags['pass']:
		dmn_dig(flags)
		dmn_whois(flags)
		dmn_ssl(flags)	
		dmn_prop(flags)
		return flags
	else:
		return False
	
def dmn_parse(flags):
	try:
		parts = flags['urlparse'].hostname.split('.')
	except AttributeError:
		flags['pass']=False
		parts = 'empty'
	
	if (len(parts) < 2 or len(parts) > 5):
		flags['pass']=False
		
	else:
		
		response = urllib2.urlopen('http://data.iana.org/TLD/tlds-alpha-by-domain.txt')
		tlds = response.read()
		tlds=[tld.strip() for tld in tlds.split()]
		
		if parts[-1].upper() in tlds:
		
			if len(parts) == 2:
				flags['domain'] = '{}.{}'.format(*parts[-2:])
			else:
				if (parts[-2].upper() in tlds and parts[-3] != 'www'):
					flags['domain'] = '{}.{}.{}'.format(*parts[-3:])
				else:
					flags['domain'] = '{}.{}'.format(*parts[-2:])
			flags['pass']=True
		else:
			flags['pass']=False
	
def dmn_dig(flags):
	digs = ('A', 'NS', 'TXT', 'MX', 'CNAME')
	for dig in digs:
		cmd = 'timeout 3 dig {} {} +nocomments +noadditional +noauthority'.format(flags['domain'], dig)
		flags['dns']+=dmn_dig_parse(dmn_run_cmd(cmd))
	
def dmn_dig_parse(retval):
	result = ''
	for line in retval.splitlines():
		line.strip()
		if (line != '' and ';' not in line):
			result += ('{}\n'.format(line))
	result += '\n'
	return result

def dmn_whois(flags):
	cmd = 'timeout 5 whois -H {}'.format(flags['domain'])
	flags['whois'] = dmn_run_cmd(cmd).splitlines()
	
def dmn_run_cmd(cmd):
	hgt_logger.info('[*] Running command : {}'.format(cmd))
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	retval = p.communicate()[0]
	return retval
	
def dmn_ssl(flags):
	cmd = 'echo "QUIT" | timeout 5 openssl s_client -connect {}:443'.format(flags['domain'])
	cmd += ' 2>/dev/null | openssl x509 -noout -text'
	flags['ssl'] = dmn_run_cmd(cmd).splitlines()
	
def dmn_prop(flags):
	srv_list = [
	['Poland', '213.25.129.35'],
	['Indonesia',  '203.29.26.248'],
	['US', '216.218.184.19', '76.12.242.28'],
	['Australia', '203.59.9.223'],
	['Brazil', '177.135.144.210'],
	['Italy', '88.86.172.11'],
	['India',  '182.71.113.34'],
	['Nigeria', '41.58.157.70'],
	['Egypt', '41.41.107.38'],
	['UK', '109.228.25.69', '80.195.168.42'],
	['Google', '8.8.8.8']]
	
	flags['prop'] = ''
	
	for test in srv_list:
		loc = test.pop(0)
		
		if isinstance(test, (list, tuple)):
			for ip in test:
				dmn_prop_append(flags, loc, ip)
		else:
			dmn_prop_append(flags, loc, test)
			
		print flags['prop']

def dmn_prop_append(flags, loc, ip):
	cmd = ('dig @{} {} +short'.format(ip, flags['domain']))
	flags['prop'] += '\n{} : {} Result\n'.format(loc, ip)
	print cmd
	flags['prop'] += dmn_dig_parse(dmn_run_cmd(cmd))

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
	
	hgt_logger.info('[*] Spark Log Search started')
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
		
# Calculate the date to return (SL section)
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

	hgt_logger.info('[*] Opening {}'.format(pl))
	
	with open(pl, "a") as passlist:
		passlist.write("{}\n".format(arg1))
		hgt_logger.debug('\tAdded : {}'.format(arg1))
		
	passlist.close()
	hgt_logger.debug('\t{} closed'.format(pl))
	
# Function to open and return PassChats file contents
def pc_readlines(pl=PASS_LIST):

	hgt_logger.info('[*] Opening {}'.format(pl))
	
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

	hgt_logger.info('[*] Testing dBus connection')

	bus = dbus.SessionBus()
	obj = bus.get_object("im.pidgin.purple.PurpleService", 
						"/im/pidgin/purple/PurpleObject")
	purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
	
	hgt_logger.info('[*] Finding Pidgin Accounts')
	
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
						hgt_logger.info('[*] Attempting to message user :{}'.format(buddy_name))
							
						conv = purple.PurpleConversationNew(1, acct, buddy_name)
						im = purple.PurpleConvIm(conv)
						purple.PurpleConvImSend(im, pc_build_msg(str(chats)))
						
						hgt_logger.debug('\tMessage Sent to {}'.format(buddy_name))
						ex_flag=True			
	
def pc_build_msg(opt):
	msg = "\nCurrently I have : " + opt + " chats to pass.\nPlease reply if you can assist!\n"
	msg = msg + "\n\t[*] This has been an automated chat pass request."
	return msg

def pc_do_test(dbg):
	
	buddy_count = 0
	acct_count = 0
	
	hgt_logger.info('[*] Testing dBus connection')
	
	bus = dbus.SessionBus()
	
	try:
		obj = bus.get_object("im.pidgin.purple.PurpleService", 
							"/im/pidgin/purple/PurpleObject")
		purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
		
		hgt_logger.debug('\tSuccess...')
		hgt_logger.info('[*] Checking for available Pidgin Buddies')
		
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
		
	retval = subprocess.check_output(cmd)
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
