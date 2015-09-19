#!/usr/bin/python
from gi.repository import GObject
from gi.repository import Gtk, Gdk
import sys, getopt, datetime, time, os
import dbus, dbus.glib, dbus.decorators
import logging
from os.path import expanduser

#******************************GLOBALS**********************************

# Logging
# Default logging configuration settings
# https://docs.python.org/2/library/logging.html#logger-objects
hgt_logger = logging.getLogger('hgtools_gtk.py')

#Pass_Chats Functionality
PASS_LIST='./lib/pc_list.txt'
DOM_SUFFIX='@openfire.houston.hostgator.com'
PURPLE_CONV_TYPE_IM=1

# Spark_Log Functionality

# HGTools Functionality

# GUI

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
	
	last_run = logging.FileHandler('./tmp/last_run.log', 'w')
	last_run.setFormatter(file_formatter)
	logger.addHandler(last_run)
	
	if level==logging.DEBUG:
		
		cons_handler = logging.StreamHandler(sys.stdout)
		cons_handler.setFormatter(cons_formatter)
		logger.addHandler(cons_handler)
	
	return logger

# Used for printing messages stored in the library files
def lib_out(e , msg):
	# If Passed "LOGO" displays the script header
	hgt_logger.debug('lib_out args : {} :: {}'.format(e, msg))
	
	lib_s = '{}{}'.format(expanduser('~'), _PATH)

	print e
	with open(lib_s, 'r') as f:
		
		for num, line in enumerate(f, 1):
			hgt_logger.debug('\tlib_out image located at {}'.format(num))
			if '<{}>'.format(msg) in line:
				break

		# Continue from the first instance
		for line in f:

			# Break on the second instance
			if '</{}>'.format(msg) in line:
				break

			# Otherwise print the line
			hgt_logger.info(line.strip("\r\n"))

# Validates the argument format if date type
def valid_date(s):
	hgt_logger.debug('\tvalid_date args : {}'.format(s))
	
	try:
		return datetime.strptime(s, "%Y-%m-%d")
	except ValueError:
		hgt_logger.error("[*] Not a valid date: '{}'.".format(s))
		sys.exit(3)
        
# Strip excess characters
def clean_line(l):
	# hgt_logger.debug('clean_line args : %s' % l)
	
	_l = str(l)
	remove = ['[[', ']]', '[', ']']
	_l.translate(None, ''.join(remove))
	return _l

# Search for files within the specified term
# (Months or specific date)
# Returns a list of files matching the criteria
def find_files(d, str_search, t=3):
	hgt_logger.debug('\tfind_files args : {} :: {}'.format(d, t))

	_dir = expanduser('~') + '/.purple/logs/jabber/'
	hgt_logger.debug('\tPidgin log path : {}'.format(_dir))

	# Check if a date was passed
	if type(d) is datetime.date:
		hgt_logger.debug('\tSearching on date : {}'.format(d))
		exact_date = d

	# If not a date, process monthly term passed
	else:
		begin_date = monthdelta(datetime.date.today(), int(t))
		hgt_logger.debug('\tSearching for term : {}'.format(d))
		exact_date = 1

	_files = []
	for dirpath, subdirs, files in os.walk(_dir, onerror=None):
		
		for f in files:
			_path = os.path.join(dirpath, f)
			
			if exact_date != 1:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) == exact_date:
					if filter_rooms(_path, str_search):
						hgt_logger.debug('\tAdding {} to the list'.format(_path))
						_files.append(_path)
						
			else:
				if datetime.date.fromtimestamp(os.path.getctime(_path)) > begin_date:
					if filter_rooms(_path, str_search):
						hgt_logger.debug('Adding {} to the list'.format(_path))
						_files.append(_path)
	
	hgt_logger.debug('\tAdded {!s} files to the list'.format(len(_files)))
	hgt_logger.debug('\tSorting files...')					
	_files.sort(key=lambda x: os.path.getmtime(x))
	return _files

# Returns all lines matching the passed term
def find_lines(str_search, _file):
	hgt_logger.debug('\tfind_lines args : {} :: {}'.format(_file, str_search))
	
	_lines = []
	look_for = ('keyword', 'user')
	keys = [i for i in look_for if i in list(str_search.keys()) and str_search[i]!=None]
	hgt_logger.debug('\tKeys found : {}'.format(keys))
	
	with open(_file, 'r') as f:
		for line in f:
			if keys:
				for key in keys:
					hgt_logger.debug('\tSearching for : {}'.format(str_search[key]))
					if line.find(str_search[key])>0:
						_lines.append('<br>' + clean_line(f.name) + '<br>')
						for _line in f:
							_lines.append(_line.rstrip())
						break
			else:
				_lines.append(line.rstrip())
	
	hgt_logger.debug('\tAdded {0!s} lines to output'.format(len(_lines)))
	return _lines

# Filter paths for room or user as specified
def filter_rooms(_path, str_search):
	
	check_for = ('room', 'user')
	found = False
	
	for key in list(str_search.keys()):
		if key in check_for:
			if (str_search[key] != None and _path.find(str_search[key]) > 0):
				hgt_logger.debug("\tFound {0} in {1}".format(str_search[key], _path))
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
	gt_logger.debug('\tMessage :\t{}'.format(msg))
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
		hgt_logger.error('[*] Details - {:}'.format(*e))
		
	
def pc_main(*argv, **kwargs):
	
	if argv is not None:
		
		if 'show' in argv:	
			lines = pc_readlines()
		
			hgt_logger.debug('[*] pc_list.txt Contents :')
			
			for line in lines:
				hgt_logger.debug('\t{}'.format(line))
		
		if 'add' in argv:
			for name, value in kwargs.items():
				if name=='add': pc_add(value)
			
		if 'remove' in argv:
			slctn=-1
			lines = pc_readlines()
			
			for idx, val in enumerate(lines):
				print str((idx+1)) + ". " + val
			
			while slctn not in range(0, len(lines)+1):
				slctn = input("Choose a line to remove : ")
			
			slctn -= 1
			
			with open(PASS_LIST, "w") as passlist:
				for idx, val in enumerate(lines):
					if idx!=slctn:
						passlist.write(val + "\n")
			
			passlist.close()
		
		# Build the list of buddies to send to	
		if 'list' in argv:
			lines = [line.strip() for line in open(PASS_LIST)]
			with open(PASS_LIST, "r") as passlist:
				lines = [line.strip() for line in passlist]
			passlist.close()
		
		# Add a specified buddy to the list	
		if 'buddy' in argv:
			for name, value in kwargs.items():
				if name=='buddy': lines.append(value)
		
		# Send the message to the list of buddies
		if ('buddy' in argv or 'list' in argv):
			for name, value in kwargs.items():
				if name=='chats': chat_count=value
			for name, value in kwargs.items():
				if name=='list': pc_pass_req(chat_count, lines)
		
#******************************/PASS_CHATS******************************

#*********************************STYLE*********************************
def gtk_style():
	css = b"""
* {
    transition-property: color, background-color, border-color, background-image, padding, border-width;
    transition-duration: 0.5s;
    font: 15px arial, sans-serif;
}
GtkWindow {
    background: linear-gradient(153deg, #151515, #151515 5px, transparent 5px) 0 0,
                linear-gradient(333deg, #151515, #151515 5px, transparent 5px) 10px 5px,
                linear-gradient(153deg, #222, #222 5px, transparent 5px) 0 5px,
                linear-gradient(333deg, #222, #222 5px, transparent 5px) 10px 10px,
                linear-gradient(90deg, #1b1b1b, #1b1b1b 10px, transparent 10px),
                linear-gradient(#1d1d1d, #1d1d1d 25%, #1a1a1a 25%, #1a1a1a 50%, transparent 50%, transparent 75%, #242424 75%, #242424);
    background-color: #131313;
    background-size: 20px 20px;
    border-style: solid;
    border-width: 5px 0 2px 2px;
    border-color: #FFF;
    font: 15px arial, sans-serif;
}
.button {
    color: black;
    background-color: #bbb;
    border-style: solid;
    border-width: 2px 0 2px 2px;
    border-color: #333;
    box-shadow: 0 0 5px #333 inset;
    padding: 12px 4px;
    font: 15px arial, sans-serif;
}
.button:first-child {
    border-radius: 2px 0 0 2px;
    font: 15px arial, sans-serif;
}
.button:last-child {
    border-radius: 0 2px 2px 0;
    border-width: 2px;
    font: 15px arial, sans-serif;
}
.button:hover {
    background-color: #4870bc;
    font: 15px arial, sans-serif;
}
.button *:hover {
    color: white;
    font: 15px arial, sans-serif;
}
.button:hover:active,
.button:active {
    background-color: #993401;
    font: 15px arial, sans-serif;
}
.GtkLabel {
	font: 15px arial, sans-serif;
}
        """
	style_provider = Gtk.CssProvider()
	style_provider.load_from_data(css)

	Gtk.StyleContext.add_provider_for_screen(
		Gdk.Screen.get_default(),
		style_provider,
		Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
#*********************************Classes*******************************
class hgt_window(Gtk.Window):
	
# Google Drive URL to diagram : https://drive.draw.io/#G0B6z1IIlV5HAPSWtrUTdjeW0tUU0

	global favicon
	
	def __init__(self):
		
		try:
			win_title = 'HG Tools'
			Gtk.Window.__init__(self, title=win_title)
			hgt_logger.debug("[*] HGTools GUI spawned")
			self.set_icon_from_file(favicon)
			
			# Widget Enumeration
			widgets = self.widget_config()
			
			# Grid/Box Constructor
			grid = Gtk.Grid()
			grid.set_border_width(1)
			grid.set_column_homogeneous(True)
			grid.set_row_homogeneous(False)
			grid.set_column_spacing(6)
			grid.set_row_spacing(6)
			self.box_config(grid, widgets)
			self.add(grid)

			self.set_position(Gtk.WindowPosition.CENTER)
			
		except Exception as e:
			hgt_logger.debug('[*] {:}'.format(e))
			Gtk.main_quit()
			
	# Signal Events

	def pc_button_exec(self, widget):
		# Execute pass_chats
		hgt_logger.debug("[*] pc_button clicked")

	def sl_button_exec(self, widget):
		# Execute spark_logs
		hgt_logger.debug("[*] sl_button clicked")
		
	def sl_chatroom_combo_changed(self, widget):
		# Chatroom Combo Changed
		hgt_logger.debug("[*] sl_chatroom_combo changed")
		
	def hgt_button_exec(self, widget):
		# Execute hgtools search
		hgt_logger.debug("[*] hgt_button clicked")
		
	def menu_cl_button_exec(self, widget):
		# Close the window
		hgt_logger.debug("[*] cl_button clicked")
		Gtk.main_quit()
		
	def menu_log_button_exec(self, widget):
		# Show the last_run log file
		hgt_logger.debug("[*] log_button clicked")
		
	def pc_add_button_exec(self, widget):
		# Add a user to the pass_chats list
		hgt_logger.debug("[*] add_button clicked")
		
	def pc_remove_button_exec(self, widget):
		# Remove a user from the pass_chats list
		hgt_logger.debug("[*] remove_button clicked")
		
	def pc_chats_combo_changed(self, widget):
		# Chat count combo changed
		hgt_logger.debug("[*] chats_combo changed")
		
	def sl_depth_combo_changed(self, widget):
		# Search depth combo changed
		hgt_logger.debug("[*] sl_depth_combo changed")
		
	def pc_chatlist_selection_changed(self, selection):
		# pc_chatlist_treeview changed
		model, treeiter = selection.get_selected()
		if treeiter != None:
			sel = model[treeiter][0]
		hgt_logger.debug("[*] pc_chatlist_selection changed to {}".format(sel))

	# Window Format

	def box_config(self, grid, widgets):
		hgt_logger.debug('[*] Configuring Boxes')
		
		hgt_top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		
		pc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		pc_widgets =  [widget for widget in widgets if '{!s}'.format(widget[0]).startswith('pc_')]
		for item in pc_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(pc_widgets) : {}'.format(len(pc_widgets)))
		self.pc_box_build(pc_box, pc_widgets)

		sl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		sl_widgets =  [widget for widget in widgets if widget[0].startswith('sl_')]
		for item in sl_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(sl_widgets) : {}'.format(len(sl_widgets)))
		self.sl_box_build(sl_box, sl_widgets)
		
		hgt_top_box.pack_start(pc_box, True, True, 0)
		hgt_top_box.pack_start(sl_box, True, True, 0)
		grid.add(hgt_top_box)

		hgt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		hgt_widgets = [widget for widget in widgets if widget[0].startswith('hgt_')]
		for item in hgt_widgets:
			hgt_logger.debug('\t\t{}'.format(item[0]))
		hgt_logger.debug('\tlen(hgt_widgets) : {}'.format(len(hgt_widgets)))
		self.hgt_box_build(hgt_box, hgt_widgets)
		grid.attach_next_to(hgt_box, hgt_top_box, Gtk.PositionType.BOTTOM, 1, 2)

		menu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		menu_widgets = [widget for widget in widgets if widget[0].startswith('menu_')]
		for item in menu_widgets:
			hgt_logger.debug('\t\t{}'.format(item[:]))
		hgt_logger.debug('\tlen(menu_widgets) : {}'.format(len(menu_widgets)))
		self.menu_box_build(menu_box, menu_widgets)
		grid.attach_next_to(menu_box, hgt_box, Gtk.PositionType.BOTTOM, 1, 2)
		
	def pc_box_build(self, pc_box, pc_widgets):
		hgt_logger.debug('\tpc_box_build')
		
		# pc_label
		pc_label = Gtk.Label(pc_widgets[0][1])
		
		# pc_chats_combo
		pc_chats_combo_store = Gtk.ListStore(str)
		for item in pc_widgets[1][1]:
			pc_chats_combo_store.append(['{!s}'.format(item)])	
		pc_chats_combo = Gtk.ComboBox.new_with_model(pc_chats_combo_store)
		pc_chats_combo.set_tooltip_text(pc_widgets[1][2])
		pc_chats_combo.connect(*pc_widgets[1][3])
		renderer_text = Gtk.CellRendererText()
		pc_chats_combo.pack_start(renderer_text, True)
		pc_chats_combo.add_attribute(renderer_text, "text", 0)
		pc_chats_combo.set_active(0)
		
		# pc_chatlist_store
		pc_chatlist_store = Gtk.ListStore(str)
		for item in pc_widgets[2][1]:
			pc_chatlist_store.append([item])
		pc_chatlist_treeview = Gtk.TreeView(pc_chatlist_store)
		renderer = Gtk.CellRendererText()
		column = Gtk.TreeViewColumn("Your List", renderer, text=0)
		column.set_sort_column_id(0)
		pc_chatlist_treeview.append_column(column)
		select = pc_chatlist_treeview.get_selection()
		select.connect("changed", self.pc_chatlist_selection_changed)
		
		# pc_remove_button
		pc_remove_button = Gtk.Button.new_with_label(pc_widgets[3][1])
		pc_remove_button.set_tooltip_text(pc_widgets[3][2])
		pc_remove_button.connect(*pc_widgets[3][3])
		
		# pc_ldap_box
		pc_ldap_box = Gtk.Entry()
		pc_ldap_box.set_text(pc_widgets[4][1])
		pc_ldap_box.set_tooltip_text(pc_widgets[4][2])
		
		# pc_add_button
		pc_add_button =  Gtk.Button.new_with_label(pc_widgets[5][1])
		pc_add_button.set_tooltip_text(pc_widgets[5][2])
		pc_add_button.connect(*pc_widgets[5][3])
		
		# pc_subbox
		pc_subbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		pc_subbox.pack_start(pc_ldap_box, True, True, 0)
		pc_subbox.pack_start(pc_add_button, True, True, 0)
		
		# pc_alert_label
		pc_alert_label = pc_label = Gtk.Label(pc_widgets[6][1])
		
		# pc_button
		pc_button =  Gtk.Button.new_with_label(pc_widgets[7][1])
		pc_button.set_tooltip_text(pc_widgets[7][2])
		pc_button.connect(*pc_widgets[7][3])
		
		pc_box.pack_start(pc_label, True, True, 0l)
		pc_box.pack_start(pc_chats_combo, True, True, 0)
		pc_box.pack_start(pc_chatlist_treeview, True, True, 0)
		pc_box.pack_start(pc_remove_button, True, True, 0)
		pc_box.pack_start(pc_subbox, True, True, 0)
		pc_box.pack_start(pc_alert_label, True, True, 0)
		pc_box.pack_start(pc_button, True, True, 0)
		
	def sl_box_build(self, sl_box, sl_widgets):
		hgt_logger.debug('\tsl_box_build')
		
		# sl_label
		sl_label = Gtk.Label(sl_widgets[0][1])
		
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
		
		# sl_keyword_box
		sl_keyword_box = Gtk.Entry()
		sl_keyword_box.set_text(sl_widgets[3][1])
		sl_keyword_box.set_tooltip_text(sl_widgets[3][2])
		
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
		
		# sl_button
		sl_button =  Gtk.Button.new_with_label(sl_widgets[6][1])
		sl_button.set_tooltip_text(sl_widgets[6][2])
		sl_button.connect(*sl_widgets[6][3])
		
		sl_box.pack_start(sl_label, True, True, 0l)
		sl_box.pack_start(sl_depth_combo, True, True, 0)
		sl_box.pack_start(sl_date_box, True, True, 0)
		sl_box.pack_start(sl_keyword_box, True, True, 0)
		sl_box.pack_start(sl_chatroom_combo, True, True, 0)
		sl_box.pack_start(sl_user_box, True, True, 0)
		sl_box.pack_start(sl_button, True, True, 0)
		
	def hgt_box_build(self, hgt_box, hgt_widgets):
		hgt_logger.debug('\thgt_box_build')
		
		# hgt_search_box
		hgt_search_box = Gtk.Entry()
		hgt_search_box.set_text(hgt_widgets[0][1])
		hgt_search_box.set_tooltip_text(hgt_widgets[0][2])
		
		# hgt_button
		hgt_button =  Gtk.Button.new_with_label(hgt_widgets[1][1])
		hgt_button.set_tooltip_text(hgt_widgets[1][2])
		hgt_button.connect(*hgt_widgets[1][3])
		
		hgt_box.pack_start(hgt_search_box, True, True, 0)
		hgt_box.pack_start(hgt_button, True, True, 0)
		
	def menu_box_build(self, menu_box, menu_widgets):
		hgt_logger.debug('\tmenu_box_build')
		
		# menu_cl_button
		menu_cl_button =  Gtk.Button.new_with_label(menu_widgets[0][1])
		menu_cl_button.set_tooltip_text(menu_widgets[0][2])
		menu_cl_button.connect(*menu_widgets[0][3])
		
		# menu_log_button
		menu_log_button =  Gtk.Button.new_with_label(menu_widgets[1][1])
		menu_log_button.set_tooltip_text(menu_widgets[1][2])
		menu_log_button.connect(*menu_widgets[1][3])
		
		menu_box.pack_start(menu_cl_button, True, True, 0)
		menu_box.pack_start(menu_log_button, True, True, 0)
		
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
							
		# pc_alert_label (For status alerts)
		hgt_widget.append(('pc_alert_label', ''))
		
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
		hgt_widget.append(('sl_user_box', 'User (LDAP)',
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
		hgt_widget.append(('hgt_button', 'Phrase Search',
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
