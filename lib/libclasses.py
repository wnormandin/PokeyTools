#!/usr/bin/python

from gi.repository import Gtk
from log import *
from libfunctions import get_resource_path

spark_logger = logging.getLogger('spark_tools.py')

#********************************GLOBALS********************************

# Button Labels
win_title = 'HG Tools'
pc_button_text = 'Broadcast'
sl_button_text = 'Search'
hgt_button_text = 'Search Scripts and AHKs'
cl_button_txt = 'Close Window'
log_button_txt = 'View Logs'
add_button_txt = 'Add'
remove_button_txt = 'Remove User'

# Text Label values
sl_label_txt = 'Spark Log Search'
pc_label_txt = 'Pass Chats'

# Chats Combo Values
chat_count_values = range(6)
chat_count_default = '# of Chats'

# HG Tools Search Box
hgt_search_default = 'Search Term'

# ToolTip text :

pc_button_tooltip = 'Broadcasts a pass_chat message to\nthe users in your list'
sl_button_tooltip = 'Search your Spark Logs with the\nspecified parameters'
hgt_button_tooltip = 'Searches for AHKs or scripts matching\nthe Search Term entered'
cl_button_tooltip = 'Closes this window'
log_button_tooltip = 'Displays the file last_run.log'
add_button_tooltip = 'Adds a user to your pass_chats list'
remove_button_tooltip = 'Removes a user from your pass_chats list'
chat_count_tooltip = 'The number of chats your\npass_chat message will show'
ldap_box_tooltip = "Enter a user's LDAP username\nto add to your pass_chat list"
search_box_tooltip = 'Specify a search term for\nyour AHK/Script search'
depth_box_tooltip = 'Specify a search term in months (Max 12)'
keyword_box_tooltip = 'Specify keyword(s) to search'
chatroom_box_tooltip = 'Specify a chat room to search'



#********************************/GLOBALS*******************************

class spark_window(Gtk.Window):

	def __init__(self):
		Gtk.Window.__init__(self, title=win_title)
		
		spark_logger.debug("HGTools GUI spawned")
		
		self.box = Gtk.Box(spacing=6)
		self.add(self.box)
		self.set_icon_from_file(get_resource_path("./images/snappyfav.png"))
		
		# Pass_Chats button
		self.pc_button = Gtk.Button(label=pc_button_text)
		self.pc_button.connect("clicked", self.pass_chats_exec)
		self.pc_button.set_tooltip_text(pc_button_tooltip)
		
		# Spark_Log button
		self.sl_button = Gtk.Button(label=sl_button_text)
		self.sl_button.connect("clicked", self.search_spark_logs)
		self.sl_button.set_tooltip_text(sl_button_tooltip)
		
		# HGTools search button
		self.hgt_button = Gtk.Button(label=hgt_button_text)
		self.hgt_button.connect("clicked", self.hgt_search_exec)
		self.hgt_button.set_tooltip_text(hgt_button_tooltip)
		
		# Close Window button
		self.cl_button = Gtk.Button(label=cl_button_txt)
		self.cl_button.connect("clicked", self.cl_button_exec)
		self.cl_button.set_tooltip_text(cl_button_tooltip)
		
		# Show log file button
		self.log_button = Gtk.Button(label=log_button_txt)
		self.log_button.connect("clicked", self.log_button_exec)
		self.log_button.set_tooltip_text(log_button_tooltip)
		
		# Add pass_chat broadcast recipient button
		self.add_button = Gtk.Button(label=add_button_txt)
		self.add_button.connect("clicked", self.add_button_exec)
		self.add_button.set_tooltip_text(add_button_tooltip)
		
		# Remove pass_chat broadcast recipient button
		self.remove_button = Gtk.Button(label=remove_button_txt)
		self.remove_button.connect("clicked", self.remove_button_exec)
		self.remove_button.set_tooltip_text(remove_button_tooltip)
		
		
		self.box.pack_start(self.pc_button, True, True, 0)
		self.box.pack_start(self.sl_button, True, True, 0)
		self.box.pack_start(self.hgt_button, True, True, 0)
		self.box.pack_start(self.cl_button, True, True, 0)
		self.box.pack_start(self.log_button, True, True, 0)
		self.box.pack_start(self.add_button, True, True, 0)
		self.box.pack_start(self.remove_button, True, True, 0)

		self.set_position(Gtk.WindowPosition.CENTER)

	def pass_chats_exec(self, widget):
		# Execute pass_chats
		spark_logger.debug("pc_button clicked")
		print("pass_chats_exec")

	def search_spark_logs(self, widget):
		# Execute spark_logs
		spark_logger.debug("sl_button clicked")
		print("search_spark_logs")
		
	def hgt_search_exec(self, widget):
		# Execute hgtools search
		spark_logger.debug("hgt_button clicked")
		print("hgt_search_exec")
		
	def cl_button_exec(self, widget):
		# Close the window
		spark_logger.debug("cl_button clicked")
		print("cl_button_exec")
		
	def log_button_exec(self, widget):
		# Show the last_run log file
		spark_logger.debug("log_button clicked")
		print("log_button_exec")
		
	def add_button_exec(self, widget):
		# Add a user to the pass_chats list
		spark_logger.debug("add_button clicked")
		print("add_button_exec")
		
	def remove_button_exec(self, widget):
		# Remove a user from the pass_chats list
		spark_logger.debug("remove_button clicked")
		print("remove_button_exec")
