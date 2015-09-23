#!/usr/bin/python
from gi.repository import GObject, Pango
from gi.repository import Gtk, Gdk
import sys, getopt, datetime, time, os
import dbus, dbus.glib, dbus.decorators
import logging, getpass, webbrowser
from os.path import expanduser
from multiprocessing import Pool
import xml.etree.ElementTree as ET

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
MAX_PROC=5

# HGTools Functionality

# GUI
ENV_USER = getpass.getuser()
CSS_PATH = './lib/hgt_win_style.css'
UI_INFO_PATH = './lib/ui_info.xml'

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

#*********************spark_log functionality***************************

def sl_main(date, term, keyword, user, room):
		
	
	hgt_logger.debug('[*] Spark Log Search started')
	
	# Define Output Path
	fpath = './.parsed/'
	hgt_logger.debug('\t Output path : {}'.format(fpath))

	_lines = []
	_opath = ('{}/dev/.spark_log/.parsed.html'.format(expanduser('~')))

	# Filter by Absolute Date or Term
	if 'date' in str_search:
		_files = sl_find_files(datetime.datetime.date(datetime.datetime.strptime(str_search['date'], '%Y-%m-%d')), str_search)
		hgt_logger.debug("\t Searching on {}".format(str_search['date']))
	else:
		_files = sl_find_files(1, str_search, str_search['term'])
		hgt_logger.debug("\t Searching the past {} months".format(str_search['term']))

	# Check for MULTIPROC and process accordingly
	hgt_logger.debug('\t MULTIPROC = {}'.format(MULTIPROC))
	if not MULTIPROC:
		for _file in _files:
			_lines.append(sl_find_lines(str_search, _file))
			hgt_logger.debug('\t File searched : {}'.format(_file))
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
				results[k] = pool.apply_async(sl_find_lines, [str_search, chunk[k]])
				
			pool.close()
			pool.join()
			
			for k in range (this_min):
				_lines.extend(results[k].get())
				
			i += this_min
			
	hgt_logger.debug('\t {} files searched'.format(len(_files)))
	hgt_logger.debug('\t {} lines found'.format(len(_lines)))

	open(_opath, 'w').close() # Empty File Contents
	hgt_logger.debug('\t {} reinitialized'.format(_opath))

	# Write new file data
	with open(_opath, 'w') as f:
		hgt_logger.debug('\t Writing {} lines'.format(len(_lines)))
		
		for l in _lines:
			f.write(sl_clean_line(l))
	f.close()
	webbrowser.open(_opath, new=2)

# Validates the argument format if date type
def valid_date(s):
	hgt_logger.debug('\t valid_date args : {}'.format(s))
	
	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		hgt_logger.error("[*] Not a valid date: '{}'.".format(s))
		ve_win = InfoDialog(self, "Invalid Date", "Not a valid date: '{}'.".format(s))
		response = ve_win.run()
		ve_win.destroy()

# Strip excess characters
def sl_clean_line(l):
	tree = ET.fromstring(str(l))
	notags = ET.tostring(tree, encoding='utf8', method='text')
	return notags

# Search for files within the specified term
# (Months or specific date)
# Returns a list of files matching the criteria
def sl_find_files(d, str_search, t=3):
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
			str_search['term']=t
		begin_date = monthdelta(datetime.date.today(), int(t))
		hgt_logger.debug('\t Searching for term : {}'.format(t))
		exact_date = 1

	_files = []
	for dirpath, subdirs, files in os.walk(_dir, onerror=None):
		
		for f in files:
			_path = os.path.join(dirpath, f)
			
			if exact_date != 1:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) == exact_date:
					if sl_filter_rooms(_path, str_search):
						_files.append(_path)	
			else:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) > begin_date:
					if sl_filter_rooms(_path, str_search):
						_files.append(_path)
	
	hgt_logger.debug('\t Added {!s} files to the list'.format(len(_files)))
	hgt_logger.debug('\t Sorting files...')					
	_files.sort(key=lambda x: os.path.getmtime(x))
	return _files

# Returns all lines matching the passed term
def sl_find_lines(str_search, _file):
	hgt_logger.debug('\t sl_find_lines pid({})'.format(os.getpid()))
	
	_lines = []
	look_for = ('keyword', 'user')
	keys = [i for i in look_for if i in list(str_search.keys())]
	
	with open(_file, 'r') as f:
		for line in f:
			if keys:
				for key in keys:
					if line.find(str_search[key])>0:
						_lines.append('<br>' + sl_clean_line(f.name) + '<br>')
						for _line in f:
							_lines.append(_line.rstrip())
						break
			else:
				_lines.append(line.rstrip())
	if len(_lines)>0:
		hgt_logger.debug('\t Added {!s} lines to output'.format(len(_lines)))
	return _lines

# Filter paths for room or user as specified
def sl_filter_rooms(_path, str_search):
	
	found = False
	
	if (str_search['room']=='Chat Room' and str_search['user']=='User LDAP'):
		found = True
	else:
		if (str_search['user']=='User LDAP' and str_search['room']!='Chat Room'):
			if (_path.find(str_search['room']) > 0):
				hgt_logger.debug("\t Found {0} in {1}".format(str_search['room'], _path))
				found = True
		elif (str_search['user']!='User LDAP' and str_search['room']=='Chat Room'):
			if (_path.find(str_search['user']) > 0):
				hgt_logger.debug("\t Found {0} in {1}".format(str_search['user'], _path))
				found = True
		elif (str_search['room']!='Chat Room' and str_search['user']!='User LDAP'):
			if (_path.find(str_search['user']) > 0 ):
				hgt_logger.debug("\t Found {0} in {1}".format(str_search['user'], _path))
				found = True
			if (_path.find(str_search['room']) > 0):
				hgt_logger.debug("\t Found {0} in {1}".format(str_search['room'], _path))
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
	
	def __init__(self):
		
		try:
			win_title = 'HG Tools | Welcome, {}!'.format(ENV_USER) 
			
			# Create dict for signal storage
			self.selected = {}
			
			Gtk.Window.__init__(self, title=win_title)
			hgt_logger.debug("[*] HGTools GUI spawned")
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
			
		except Exception as e:
			if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
				nf_win = InfoDialog(self, "Error", 'Details : {:}'.format(*e))
				response = nf_win.run()
				nf_win.destroy()
			hgt_logger.error('[*] Details - {:}'.format(*e))
			
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
		])
		
	def add_option_menu_actions(self, action_group):
		action_group.add_actions([
			("OptionMenu", None, " Options |"),])
		action_group.add_toggle_actions([
			("DebugMode", None, "Debug Logging", None, 
			"Turn on/off verbose logging", self.on_debugmode),])

	def on_debugmode(self, widget):
		hgt_logger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))
		if widget.get_active():
			hgt_logger.setLevel(logging.DEBUG)
			hgt_logger.debug("\t Debug Logging ON")
		else:
			hgt_logger.debug("\t Debug Logging OFF")
			hgt_logger.setLevel(logging.WARNING)

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
		if self.selected['chatcount']!='# of Chats':
			pc_main(list=True, chats=self.selected['chatcount'])
		else:
			nf_win = InfoDialog(self, "Error", 'Select a chat count')
			response = nf_win.run()
			nf_win.destroy()

	def sl_button_exec(self, widget):
		# Execute spark_logs
		hgt_logger.debug("[*] MainWindow > Log Search button clicked")
		if 'term' in self.selected:
			if self.selected['term']=='# of Months':
				self.selected['term']='3'
		if 'user' not in self.selected:
			self.selected['user']='User LDAP'
		if 'room' not in self.selected:
			self.selected['room']='Chat Room'
		sl_main(**self.selected)
		
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
		user_ldap = self.selected['pc_ldap_box']
		pc_addline(user_ldap)
		self.pc_ldap_box.set_text('Added!')
		time.sleep(1)
		self.pc_ldap_box.set_text('User LDAP')
		self.pc_list_refresh(widget)
		
		
	def pc_remove_button_exec(self, widget):
		# Remove a user from the pass_chats list
		hgt_logger.debug("[*] remove_button clicked")
		slctn = self.selected['user_selected']
		lines = pc_readlines()
		with open(PASS_LIST, "w") as passlist:
			for idx, val in enumerate(lines):
				if val!=slctn:
					passlist.write(val + "\n")
		passlist.close()
		self.pc_list_refresh(widget)
		
	def pc_chats_combo_changed(self, combo):
		# Chat count combo changed
		hgt_logger.debug("[*] MainWindow > Chat Count combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			hgt_logger.debug("\t Selected Chat Count = {}".format(name))
		self.selected['chatcount']=name
		
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
		for item in self.pc_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(pc_widgets) : {}'.format(len(self.pc_widgets)))
		self.pc_box_build(self.pc_box, self.pc_widgets)
		self.pc_box.set_homogeneous(False)

		sl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		sl_widgets =  [widget for widget in widgets if widget[0].startswith('sl_')]
		for item in sl_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(sl_widgets) : {}'.format(len(sl_widgets)))
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

		hgt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		hgt_widgets = [widget for widget in widgets if widget[0].startswith('hgt_')]
		for item in hgt_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(hgt_widgets) : {}'.format(len(hgt_widgets)))
		self.hgt_box_build(hgt_box, hgt_widgets)
		grid.attach_next_to(hgt_box, hgt_top_grid, Gtk.PositionType.BOTTOM, 1, 2)
		hgt_box.set_homogeneous(False)

		menu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
		menu_widgets = [widget for widget in widgets if widget[0].startswith('menu_')]
		for item in menu_widgets:
			hgt_logger.debug('\t\t{}'.format(item[:]))
		hgt_logger.debug('\tlen(menu_widgets) : {}'.format(len(menu_widgets)))
		self.menu_box_build(menu_box, menu_widgets)
		grid.attach_next_to(menu_box, hgt_box, Gtk.PositionType.BOTTOM, 1, 2)
		menu_box.set_homogeneous(False)
		
	def pc_box_build(self, pc_box, pc_widgets):
		hgt_logger.debug('\tpc_box_build')
		
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
		self.pc_ldap_box.connect("changed", self.pc_ldap_callback, self.pc_ldap_box)
		
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
		sl_label = Gtk.Label()
		sl_label.set_label(sl_widgets[0][1])
		
		# sl_depth_combo
		sl_depth_combo_store = Gtk.ListStore(str)
		for item in sl_widgets[1][1]:
			sl_depth_combo_store.append(['{!s}'.format(item)])
		sl_depth_combo = Gtk.ComboBox.new_with_model(sl_depth_combo_store)
		sl_depth_combo.set_tooltip_text(sl_widgets[1][2])
		sl_depth_combo.connect(*sl_widgets[1][3])
		sl_depth_combo.set_entry_text_column(0)
		renderer_text = Gtk.CellRendererText()
		sl_depth_combo.pack_start(renderer_text, True)
		sl_depth_combo.add_attribute(renderer_text, "text", 0)
		sl_depth_combo.set_active(0)
		
		# sl_date_box
		sl_date_box = Gtk.Entry()
		sl_date_box.set_text(sl_widgets[2][1])
		sl_date_box.set_tooltip_text(sl_widgets[2][2])
		sl_date_box.connect("changed", self.sl_date_callback, sl_date_box)
		
		# sl_keyword_box
		sl_keyword_box = Gtk.Entry()
		sl_keyword_box.set_text(sl_widgets[3][1])
		sl_keyword_box.set_tooltip_text(sl_widgets[3][2])
		sl_keyword_box.connect('changed', self.sl_keyword_callback, sl_keyword_box)
		
		# sl_chatroom_combo
		sl_chatroom_combo_store = Gtk.ListStore(str)
		for item in sl_widgets[4][1]:
			sl_chatroom_combo_store.append([item])	
		sl_chatroom_combo = Gtk.ComboBox.new_with_model(sl_chatroom_combo_store)
		sl_chatroom_combo.set_tooltip_text(sl_widgets[4][2])
		sl_chatroom_combo.connect(*sl_widgets[4][3])
		renderer_text = Gtk.CellRendererText()
		sl_chatroom_combo.pack_start(renderer_text, True)
		sl_chatroom_combo.add_attribute(renderer_text, "text", 0)
		sl_chatroom_combo.set_active(0)
		
		# sl_user_box
		sl_user_box = Gtk.Entry()
		sl_user_box.set_text(sl_widgets[5][1])
		sl_user_box.set_tooltip_text(sl_widgets[5][2])
		sl_user_box.connect('changed', self.sl_user_callback, sl_user_box)
		
		# sl_button
		sl_button =  Gtk.Button.new_with_label(sl_widgets[6][1])
		sl_button.set_tooltip_text(sl_widgets[6][2])
		sl_button.connect(*sl_widgets[6][3])
		
		sl_box.pack_start(sl_label, True, True, 1)
		sl_box.pack_start(sl_depth_combo, True, True, 1)
		sl_box.pack_start(sl_date_box, True, True, 1)
		sl_box.pack_start(sl_keyword_box, True, True, 1)
		sl_box.pack_start(sl_chatroom_combo, True, True, 1)
		sl_box.pack_start(sl_user_box, True, True, 1)
		sl_box.pack_start(sl_button, True, True, 1)
		
	def hgt_box_build(self, hgt_box, hgt_widgets):
		hgt_logger.debug('\thgt_box_build')
		
		# hgt_search_box
		hgt_search_box = Gtk.Entry()
		hgt_search_box.set_text(hgt_widgets[0][1])
		hgt_search_box.set_tooltip_text(hgt_widgets[0][2])
		hgt_search_box.connect("changed", self.hgt_enter_callback, hgt_search_box)
		
		# hgt_button
		hgt_button =  Gtk.Button.new_with_label(hgt_widgets[1][1])
		hgt_button.set_tooltip_text(hgt_widgets[1][2])
		hgt_button.connect(*hgt_widgets[1][3])
		
		hgt_box.pack_start(hgt_search_box, True, True, 0)
		hgt_box.pack_start(hgt_button, False, False, 0)
		
	def hgt_enter_callback(self, widget, entry):
		entry_text = entry.get_text()
		self.selected['hgt_search_term']=entry_text
		hgt_logger.debug('\t hgt_search_term = {}'.format(entry_text))
		
	def sl_date_callback(self, widget, entry):
		entry_text = entry.get_text()
		if entry_text != 'Date':
			if valid_date(entry_text):
				self.selected['date']=entry_text
				hgt_logger.debug('\t {} = {}'.format('date', entry_text))
		
	def sl_keyword_callback(self, widget, entry):
		entry_text = entry.get_text()
		if entry_text !='Keyword(s)':
			self.selected['keyword']=entry_text
			hgt_logger.debug('\t {} = {}'.format('keyword', entry_text))
		
	def pc_ldap_callback(self, widget, entry):
		entry_text = entry.get_text()
		self.selected['pc_ldap_box']=entry_text
		hgt_logger.debug('\t {} = {}'.format('pc_ldap_box', entry_text))
		
	def sl_user_callback(self, widget, entry):
		entry_text = entry.get_text()
		self.selected['user']=entry_text
		hgt_logger.debug('\t {} = {}'.format('user', entry_text))
		
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

		if 'hgt_search_term' in self.selected:
				hgt_logger.debug("\t Search Term : {}".format(self.selected['hgt_search_term']))
		else:
			hgt_logger.debug("\t No Term Specified")
			nf_win = InfoDialog(self, "No Term Specified", "Please enter a valid search term")
			response = nf_win.run()
			nf_win.destroy()
