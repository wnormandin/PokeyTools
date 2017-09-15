#!/usr/bin/python
import logging
from gi.repository import Gtk, Gdk
from gi.repository import GObject, Pango
import dbus, dbus.glib, dbus.decorators

import users
import passchats
import dbsearch
import utils
import sparklog
import domain
import hgfix

UI_INFO_PATH = './lib/ui_info.xml'
LAST_RUN_PATH = '../tmp/pokeytools.log'

#Pass_Chats Functionality
PASS_LIST='./lib/pc_list.txt'
DOM_SUFFIX='@chat.domain.com'
PURPLE_CONV_TYPE_IM=1


#*********************************STYLE*********************************
def gtk_style(css_path):

	style_provider = Gtk.CssProvider()
	css = open(css_path, 'rb')
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

pokeylogger = logging.getLogger('pokeylogger')

#***********************************************************************
#******************************MainWindow*******************************
#***********************************************************************
#
# DEPENDENCIES
#
# Required module(s)	: logging, Gtk (from gi.repository), HTMLParser
# UI Information	: ui_info.xml
# 

class MainWindow(Gtk.Window):

	global MAX_PROC
	global MULTIPROC
	global USER_SELECTION

	def __init__(self, u, favicon, level=logging.DEBUG):

		try:
			pokeylogger.setLevel(level)

			## USER INIT
			pokeylogger.debug('[*] Loading User...')
			self.user_level = users.user_main(u)
			self.user = u
			self.favicon = favicon

			## WINDOW INIT
			self.status_update()

			self.selected = {}
			self.set_name("hgt_window") # Set CSS-Equivalent ID
			self.set_icon_from_file(favicon)
			Gtk.Window.__init__(self, title=self.win_title)
			self.set_position(Gtk.WindowPosition.CENTER)
			grid = Gtk.Grid()
			widgets = self.widget_config()

			## MENU BAR
			self.action_group = Gtk.ActionGroup("menu_actions")
			self.add_menu_actions(self.action_group)
			self.uimanager = self.create_ui_manager()
			self.uimanager.insert_action_group(self.action_group)
			menubar = self.uimanager.get_widget("/MenuBar")
			# Initialize Menu Access
			self.menu_init()

			## BOXES
			self.pc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
			self.box_config(menubar, grid, widgets)

			## GRID
			grid.set_border_width(1)
			grid.set_column_homogeneous(False)
			grid.set_row_homogeneous(False)
			grid.set_column_spacing(10)
			grid.set_row_spacing(10)
			self.add(grid)

			pokeylogger.debug("[*] HGTools GUI spawned")

		except Exception as e:
			raise

#***********************************************************************
#***************************Window Config*******************************
	def status_update(self, msg=None):
			if msg == None:
				self.win_title = 'HG Tools | Welcome, {} ({})!'.format(self.user, self.user_level) 
			else:
				self.win_title = msg
			Gtk.Window.__init__(self, title=self.win_title)

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
			raise
			#self.err_raise(e)

	def box_config(self, menubar, grid, widgets):
		pokeylogger.info('[*] Configuring Boxes')

		hgt_top_grid = Gtk.Grid()

		self.pc_widgets =  [widget for widget in widgets if '{!s}'.format(widget[0]).startswith('pc_')]
		pokeylogger.debug('\t len(pc_widgets) : {}'.format(len(self.pc_widgets)))
		self.pc_box_build(self.pc_box, self.pc_widgets)
		self.pc_box.set_homogeneous(False)

		sl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		sl_widgets =  [widget for widget in widgets if widget[0].startswith('sl_')]
		pokeylogger.debug('\t len(sl_widgets) : {}'.format(len(sl_widgets)))
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
		pokeylogger.debug('\t len(hgt_widgets) : {}'.format(len(hgt_widgets)))
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
		pokeylogger.debug('\t len(menu_widgets) : {}'.format(len(menu_widgets)))
		self.menu_box_build(menu_box, menu_widgets)
		grid.attach_next_to(menu_box, self.hgt_opt2_box, Gtk.PositionType.BOTTOM, 1, 2)
		menu_box.set_homogeneous(False)

	def pc_box_build(self, pc_box, pc_widgets):
		pokeylogger.debug('\t pc_box_build')

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

		# pc_msg_box
		self.pc_msg_box = Gtk.Entry()
		self.pc_msg_box.set_text(pc_widgets[2][1])
		self.pc_msg_box.set_tooltip_text(pc_widgets[2][2])

		# pc_chatlist_store
		self.pc_chatlist_store = Gtk.ListStore(str)
		for item in pc_widgets[3][1]:
			self.pc_chatlist_store.append([item])
		self.pc_chatlist_treeview = Gtk.TreeView(self.pc_chatlist_store)
		self.renderer = Gtk.CellRendererText()
		self.column = Gtk.TreeViewColumn("Your List", self.renderer, text=0)
		self.column.set_sort_column_id(0)
		self.pc_chatlist_treeview.append_column(self.column)
		self.select = self.pc_chatlist_treeview.get_selection()
		self.select.connect("changed", self.pc_chatlist_selection_changed)

		# pc_remove_button
		self.pc_remove_button = Gtk.Button.new_with_label(pc_widgets[4][1])
		self.pc_remove_button.set_tooltip_text(pc_widgets[4][2])
		self.pc_remove_button.connect(*pc_widgets[4][3])

		# pc_ldap_box
		self.pc_ldap_box = Gtk.Entry()
		self.pc_ldap_box.set_text(pc_widgets[5][1])
		self.pc_ldap_box.set_tooltip_text(pc_widgets[5][2])

		# pc_add_button
		self.pc_add_button =  Gtk.Button.new_with_label(pc_widgets[6][1])
		self.pc_add_button.set_tooltip_text(pc_widgets[6][2])
		self.pc_add_button.connect(*pc_widgets[6][3])

		# pc_subbox
		self.pc_subbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		self.pc_subbox.pack_start(self.pc_ldap_box, True, True, 1)
		self.pc_subbox.pack_start(self.pc_add_button, True, True, 1)

		# pc_button
		self.pc_button =  Gtk.Button.new_with_label(pc_widgets[7][1])
		self.pc_button.set_tooltip_text(pc_widgets[7][2])
		self.pc_button.connect(*pc_widgets[7][3])

		self.pc_box.pack_start(self.pc_label, True, True, 1)
		self.pc_box.pack_start(self.pc_chats_combo, True, True, 1)
		self.pc_box.pack_start(self.pc_msg_box, True, True, 1)
		self.pc_box.pack_start(self.pc_chatlist_treeview, True, True, 1)
		self.pc_box.pack_start(self.pc_remove_button, True, True, 1)
		self.pc_box.pack_start(self.pc_subbox, True, True, 1)
		self.pc_box.pack_start(self.pc_button, True, True, 1)

	def pc_list_refresh(self, widget):
		store = Gtk.ListStore(str)
		for item in passchats.pc_readlines():
			store.append([item])
		self.pc_chatlist_treeview.set_model(store)

	def sl_box_build(self, sl_box, sl_widgets):
		pokeylogger.debug('\tsl_box_build')

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

        # Pack the elements into the graphical box
		sl_box.pack_start(self.sl_label, True, True, 1)
		sl_box.pack_start(self.sl_depth_combo, True, True, 1)
		sl_box.pack_start(self.sl_date_box, True, True, 1)
		sl_box.pack_start(self.sl_keyword_box, True, True, 1)
		sl_box.pack_start(self.sl_chatroom_combo, True, True, 1)
		sl_box.pack_start(self.sl_user_box, True, True, 1)
		sl_box.pack_start(self.sl_button, True, True, 1)

	def hgt_opt_box_build(self, hgt_opt_box):
		pokeylogger.debug('\t hgt_opt_box')

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
		pokeylogger.debug('\t hgt_opt_box')

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
		pokeylogger.debug('\t hgt_box_build')

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
		pokeylogger.debug('\t menu_box_build')

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
		pokeylogger.info('[*] Configuring Widgets')

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
		pokeylogger.debug('\tpc_section_widgets')
		# Pass Chats Section
		# pc_label (Section title label)
		hgt_widget.append(('pc_label', 'Pass Chats'))

		# pc_chats_combo widget (Combo Box)
		pc_chats_combo_values = []
		pc_chats_combo_values.append('# of Chats')
		pc_chats_combo_values.extend(range(6))

		hgt_widget.append(('pc_chats_combo', pc_chats_combo_values,
							'The custom string your\npass_chat message will show',
							["changed", self.pc_chats_combo_changed]))

		# pc_msg_box widget (Entry Box)
		hgt_widget.append(('pc_msg_box', 'Custom Message',
							"Enter a custom message to the\nusers in your list"))

		# pc_chatlist_treeview (Selectable TreeView list)
		hgt_widget.append(('pc_chatlist_treeview', 
							[line for line in passchats.pc_readlines()],
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
		pokeylogger.debug('\tsl_section_widgets')

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
							'Search your chat logs with the\nspecified parameters',
							["clicked", self.sl_button_exec]))

	def hgt_section_widgets(self, hgt_widget):
		pokeylogger.debug('\thgt_section_widgets')

		# HGTools Search Section
		# hgt_search_box (Entry Box)
		hgt_widget.append(('hgt_search_box', 'Search Term', 
							'Specify a search term'))

		# hgt_button (Action Button)
		hgt_widget.append(('hgt_button', 'Predefine Search',
							'Searches for HGTools with text matching\nthe search term',
							["clicked", self.hgt_button_exec]))

	def menu_section_widgets(self, hgt_widget):
		pokeylogger.debug('\tmenu_section_widgets')

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

	def err_raise(self,e):
		pokeylogger.error("[*] Exception Captured")
		#if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
			#nf_win = InfoDialog(self.favicon, self, "Error", 'Details : {:}'.format(*e))
			#response = nf_win.run()
			#nf_win.destroy()
		#else:
			#raise
		raise
		pokeylogger.error('[*] Details - {:}'.format(*e))

#***********************************************************************
#***************************Dialog Config*******************************
	def add_filters(self, dialog):
		filter_csv = Gtk.FileFilter()
		filter_csv.set_name("CSV files")
		filter_csv.add_mime_type("text/csv")
		dialog.add_filter(filter_csv)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)

#***********************************************************************
#***************************Signal Actions******************************
	def on_menu_file_csv_import(self, widget):
				pokeylogger.debug("[*] FileDialog Spawned!")
				dialog = Gtk.FileChooserDialog("Please choose a CSV file", self,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
					Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

				self.add_filters(dialog)

				response = dialog.run()
				if response == Gtk.ResponseType.OK:
					pokeylogger.debug("\t FileDialog > Open clicked")
					pokeylogger.debug("\t File selected: {}".format(dialog.get_filename()))
				elif response == Gtk.ResponseType.CANCEL:
					pokeylogger.debug("\t FileDialog > Cancel clicked")

				dialog.destroy()

	def on_domain_reports(self, widget):
		flags = domain.dmn_main()
		if flags:
			domain_window = DomainInfoDialog(self, self.favicon, flags)
			result = domain_window.run()
			domain_window.destroy()
		else:
			raise
			#err_window = InfoDialog(None, 'URL Error', 'The provided URL could not be parsed,\nplease be more specific\n\nHint : Select URL from your browser URL bar and hit CTRL+C before running')
			#result = err_window.run()
			#err_window.destroy()

	def on_csv_export(self, menuitem):
		pokeylogger.debug("[*] CSVFileDialog Spawned!")
		self.status_update('CSV Export running')
		dialog = Gtk.FileChooserDialog("Please choose a CSV file", self,
			Gtk.FileChooserAction.SAVE,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		self.add_filters(dialog)
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			pokeylogger.debug("\t FileDialog > Open clicked")
			ofile = dialog.get_filename()
			pokeylogger.debug("\t File selected: {}".format(ofile))
			dialog.destroy()
			iahk_csv_export(ofile)
		elif response == Gtk.ResponseType.CANCEL:

			pokeylogger.debug("\t FileDialog > Cancel clicked")
		dialog.destroy()
		self.status_update()

	def on_debugmode(self, widget):
		pokeylogger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))
		if widget.get_active():
			pokeylogger.setLevel(logging.DEBUG)
			pokeylogger.debug("\t Debug Logging ON")
		else:
			pokeylogger.debug("\t Debug Logging OFF")
			pokeylogger.setLevel(logging.WARNING)

	def on_clone_ahks(self, menuitem):
		pokeylogger.info('[*] Cloning user autokeys')

		# Prompt with mass upload warning
		nf_win = InfoDialog(self, "Notice", 'This may take a few minutes.')
		response = nf_win.run()
		nf_win.destroy()
		iahk_import_ahk()
		nf_win = InfoDialog(self, "Done", 'Operation Completed.')
		response = nf_win.run()
		nf_win.destroy()

	def on_maxprocs_changed(self, widget, current):
		pokeylogger.debug("\t Max procs changed to : {}".format(current.get_name()[-1]))
		global MAX_PROC
		MAX_PROC = int(current.get_name()[-1])

	def on_multiproc(self, widget):
		pokeylogger.debug("\t Multiprocessing set to : {}".format(widget.get_active()))
		global MULTIPROC
		MULTIPROC = widget.get_active()

	def on_menu_deduplicate(self, widget):
		pokeylogger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))

	def on_menu_file_quit(self, widget):
		pokeylogger.debug("[*] File > Quit Selected")
		Gtk.main_quit()

	def on_menu_others(self, widget):
		pokeylogger.debug("[*] Menu item {} {}".format(widget.get_name(), " was selected"))

	def on_menu_choices_changed(self, widget, current):
		pokeylogger.debug("[*] {} {}".format(current.get_name(), " was selected."))

	def on_menu_choices_toggled(self, widget):
		if widget.get_active():
			pokeylogger.debug("[*] {} {}".format(widget.get_name(), " activated"))
		else:
			pokeylogger.debug("[*] {} {}".format(widget.get_name(), " deactivated"))

	def pc_button_exec(self, widget):
		# Execute pass_chats
		pokeylogger.debug("[*] MainWindow > Broadcast button clicked")
		if self.selected['chats']!='# of Chats':
			passchats.pc_main(list=True, chats=self.selected['chats'])
		else:
			nf_win = InfoDialog(self, favicon, "Error", 'Select a chat count')
			response = nf_win.run()
			nf_win.destroy()

	def sl_button_exec(self, widget):
		# Execute spark_logs
		pokeylogger.debug("[*] MainWindow > Log Search button clicked")

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
		sparklog.sl_main(**sl_vars)

	def sl_chatroom_combo_changed(self, combo):
		# Chatroom Combo Changed
		pokeylogger.debug("[*] MainWindow > Chatroom combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			pokeylogger.debug("\t Selected Chatroom = {}".format(name))
		self.selected['room']=name

	def menu_cl_button_exec(self, widget):
		# Close the window
		pokeylogger.debug("[*] MainWindow > Close button clicked")
		Gtk.main_quit()

	def menu_log_button_exec(self, widget):
		# Show the last_run log file
		pokeylogger.debug("[*] log_button clicked")
		log_win = LogViewWindow(self, self.favicon)
		log_win.connect("delete-event", Gtk.main_quit)
		pokeylogger.info('[*] Showing LogViewWindow')
		log_win.show_all()
		pokeylogger.info('[*] Entering Gtk.main()')
		Gtk.main()

	def pc_add_button_exec(self, widget):
		# Add a user to the pass_chats list
		pokeylogger.debug("[*] add_button clicked")

		if self.pc_ldap_box.get_text():
			self.selected['pc_ldap_box'] = self.pc_ldap_box.get_text()
		else:
			self.selected['pc_ldap_box'] = ''

		user_ldap = self.selected['pc_ldap_box']
		passchats.pc_addline(user_ldap)
		self.pc_ldap_box.set_text('Added!')
		self.pc_ldap_box.set_text('User LDAP')
		self.pc_list_refresh(widget)

	def menu_init(self):
		disabled = ('FileNewStandard', 'DataDeduplicate')#,
							#'CloneAHKLib')
		if self.user_level != 'ADMIN':
			for action in disabled:
				this_act = self.action_group.get_action(action)
				self.deactivate(this_act)

	def deactivate(self, widget):
		widget.set_sensitive(False)

	def activate(self, widget):
		widget.set_sensitive(True)

	def pc_remove_button_exec(self, widget):
		# Remove a user from the pass_chats list
		pokeylogger.debug("[*] remove_button clicked")

		if 'user_selected' in self.selected:
			slctn = self.selected['user_selected']
			lines = passchats.pc_readlines()
			with open(PASS_LIST, "w") as passlist:
				for idx, val in enumerate(lines):
					if val!=slctn:
						passlist.write(val + "\n")
			passlist.close()
			self.pc_list_refresh(widget)
		else:
			pokeylogger.debug("\t No user specified!")
			nf_win = InfoDialog(self, self.favicon, "No user specified", "Please specify a user to remove!")
			response = nf_win.run()
			nf_win.destroy()

	def pc_chats_combo_changed(self, combo):
		# Chat count combo changed
		pokeylogger.debug("[*] MainWindow > Chat Count combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			pokeylogger.debug("\t Selected Chat Count = {}".format(name))
		self.selected['chats']=name

	def sl_depth_combo_changed(self, combo):
		# Search depth combo changed
		pokeylogger.debug("[*] MainWindow > Month Count combo changed")
		tree_iter = combo.get_active_iter()
		if tree_iter != None:
			model = combo.get_model()
			name = model[tree_iter][0]
			pokeylogger.debug("\t Selected Term  = {} months".format(name))
			self.selected['term']=name

	def pc_chatlist_selection_changed(self, selection):
		# pc_chatlist_treeview changed
		model, treeiter = selection.get_selected()
		if treeiter != None:
			sel = model[treeiter][0]
			pokeylogger.debug("[*] MainWindow > Your List > Selection changed to {}".format(sel))
			self.selected['user_selected']=sel

	def on_hgt_restype_toggled(self, radio, name):
		if radio.get_active():
			pokeylogger.debug('\t {}'.format(name))
			self.selected['hgt_rtype']=name

	def on_hgt_dest_toggled(self, radio, name):
		if radio.get_active():
			pokeylogger.debug('\t {}'.format(name))
			self.selected['hgt_dest']=name

	def hgt_button_exec(self, widget):
	# Execute hgtools search
		pokeylogger.debug("[*] MainWindow > Phrase Search clicked")

		if self.hgt_search_box.get_text():
			search_term=self.hgt_search_box.get_text()
			pokeylogger.debug("\t Search Term : {}".format(search_term))
			str_sql = 'SELECT hgt_code, hgt_text, hgt_desc FROM hgtools '
			str_sql += 'LEFT JOIN hgtools_codes ON hgt_code = hgtools_codes.code '
			str_sql += 'WHERE (hgt_text like "%{}%" OR hgt_code like "%{}%") GROUP BY hgt_code;'.format(search_term, search_term)
			outp=dbsearch.hgt_query(str_sql, 'phrases')

			# pokeylogger.debug("\t {}".format(outp))
			store = Gtk.ListStore(str, str, str)

			for line in outp.split('\n'):
				listed = line.split('\t')
				if listed != ['']:
					# pokeylogger.debug(listed)
					store.append(listed)

			if len(store)>0:
				search_win = SearchResultDialog(self, store)
				response = search_win.run()
				if response == Gtk.ResponseType.OK:
					pokeylogger.debug("\t Selected : {}".format(USER_SELECTION))
					search_win.destroy()
					try:
						if self.selected['hgt_dest'] == '2':
							dest = 'clipboard'
						else:
							dest = 'mouse'

						if self.selected['hgt_rtype'] == '1':
							src = 'Text'
							hgfix.hgfix_do_paste(USER_SELECTION, dest)
						else:
							src = 'HGFix URL'
							hgfix.hgfix_main(USER_SELECTION, dest)

						pokeylogger.debug("\t Response : {} - {} > {}".format(src, USER_SELECTION, dest))

					except Exception as e:
						raise
						# err_raise(e)
				else:
					pokeylogger.debug("\t User Cancelled Dialog")
					search_win.destroy()

			else:
				pokeylogger.debug("\t Term not found!")
				nf_win = InfoDialog(self, self.favicon, "Not Found", "No results for the specified search term!")
				response = nf_win.run()
				nf_win.destroy()

		else:
			pokeylogger.debug("\t No Term Specified")
			nf_win = InfoDialog(self, self.favicon, "No Term Specified", "Please enter a valid search term")
			response = nf_win.run()
			nf_win.destroy()

#***********************************************************************
#***************************MenuBar Actions*****************************

	def add_menu_actions(self, action_group):

		# Enumerate menu options
		self.add_file_menu_actions(self.action_group)
		self.add_data_menu_actions(self.action_group)
		self.add_option_menu_actions(self.action_group)
		self.add_domain_menu_actions(self.action_group)

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
				self.on_clone_ahks),
			("CSVExport", None, "Save Predefine Library to CSV", None, None,
				self.on_csv_export)
		])

	def add_domain_menu_actions(self, action_group):
		action_group.add_actions([
			("DomainMenu", None, " Domains |"),
			("DomainReports", None, "Domain Reports", None, None,
				self.on_domain_reports)])

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

#***********************************************************************
#***************************END MAIN WINDOW*****************************

class DedupeSelectionWindow(Gtk.Window):

	def __init__(self, parent, liststore, stats):

		Gtk.Window.__init__(self, title="HGTools Deduplication Window")
		self.set_transient_for(parent)
		pokeylogger.debug("HGTools Deduplication Window")
		pokeylogger.debug("Building grid")
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

		pokeylogger.debug("Attaching columns")
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

		pokeylogger.debug("Attaching buttons")
		# Attach Buttons	
		for i, button in enumerate(self.buttons[1:]):
			self.grid.attach_next_to(button, self.buttons[i], 
								Gtk.PositionType.RIGHT, 1, 1)

		pokeylogger.debug("Attaching labels")
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

		pokeylogger.debug("Showing window")
		# Add the treelist in a scrollable window, center and show					
		self.scrollable_treelist.add(self.treeview)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.show_all()

	# Set button click events	
	def on_selection_button_clicked(self, widget):

		button_selection = widget.get_label()
		pokeylogger.debug("Button clicked : %s" % button_selection)

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
					pokeylogger.debug("Selected : %s" % model[it][1])
			else:
				if model[it][1] in self.selected:
					self.selected.remove(model[it][1])
					pokeylogger.debug("Deselected : %s" % model[it][1])

	def delete_event(self, widget, event, data=None):
		pokeylogger.debug("Window deleted")
		Gtk.main_quit()

	def on_destroy(self, widget):
		pokeylogger.debug("Window destroyed")
		Gtk.main_quit()

class DomainInfoDialog(Gtk.Dialog):

	def __init__(self, parent, favicon, flags):
		Gtk.Dialog.__init__(self, "Domain Name Information", parent,
			Gtk.DialogFlags.MODAL, buttons=(
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		self.set_default_size(500, 500)
		self.set_icon_from_file(favicon)

		self.box = self.get_content_area()
		self.label1 = Gtk.Label('Original Input : {}'.format(flags['url']))
		self.notebook = Gtk.Notebook()

		tabs = ('dns', 'whois', 'ssl', 'prop')

		for tab in tabs:
			txt = ''
			if isinstance(flags[tab], (list, tuple)):
				for part in flags[tab]:
					txt += '{}\n'.format(part)
			else:
				txt = flags[tab]
			label = Gtk.Label(label='  {}  '.format(tab.upper()))
			self.notebook.append_page(self.create_textview(txt), label)

		self.box.add(self.notebook)
		self.box.add(self.label1)
		self.show_all()

	def create_box(self, tab):
		box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		return box

	def create_textview(self, txt):
		scrolledwindow = Gtk.ScrolledWindow()
		scrolledwindow.set_hexpand(True)
		scrolledwindow.set_vexpand(True)

		self.textview = Gtk.TextView()
		self.textbuffer = self.textview.get_buffer()
		self.textbuffer.set_text(txt)
		scrolledwindow.add(self.textview)
		return scrolledwindow

class InfoDialog(Gtk.Dialog):

	def __init__(self, favicon, parent, ttl, msg):
		Gtk.Dialog.__init__(self, ttl, parent, 0,
			(Gtk.STOCK_OK, Gtk.ResponseType.OK))
		self.set_transient_for(parent)

		self.set_default_size(150, 100)
		self.set_icon_from_file(favicon)

		label = Gtk.Label(msg)

		box = self.get_content_area()
		box.add(label)
		self.show_all()

class SearchDialog(Gtk.Dialog):

	def __init__(self, parent, favicon):
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

	def __init__(self, parent, favicon):
		Gtk.Window.__init__(self, title=LAST_RUN_PATH)
		self.set_transient_for(parent)
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
			pokeylogger.debug("[*] SearchDialog > Cancel clicked")
			dialog.destroy()

		if response == Gtk.ResponseType.OK:
			pokeylogger.debug("[*] SearchDialog > Find clicked")
			cursor_mark = self.textbuffer.get_insert()
			start = self.textbuffer.get_iter_at_mark(cursor_mark)
			if start.get_offset() == self.textbuffer.get_char_count():
				start = self.textbuffer.get_start_iter()
			search_term = dialog.entry.get_text()
			pokeylogger.debug("\t Search term : {}".format(search_term))
			self.search_and_mark(search_term, start)
		dialog.destroy()

	def search_and_mark(self, text, start):
		end = self.textbuffer.get_end_iter()
		match = start.forward_search(text, 0, end)

		if match != None:
			match_start, match_end = match
			self.textbuffer.apply_tag(self.tag_found, match_start, match_end)
			self.search_and_mark(text, match_end)

class SearchResultDialog(Gtk.Dialog):

	global USER_SELECTION

	def __init__(self, parent, store):
		Gtk.Dialog.__init__(self, "Select a record", parent, 0,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

		tree = Gtk.TreeView(store)
		renderer = Gtk.CellRendererText()
		renderer.props.wrap_width = 800
		scrollable_treelist = Gtk.ScrolledWindow()
		scrollable_treelist.set_vexpand(True)
		scrollable_treelist.set_hexpand(True)
		scrollable_treelist.set_border_width(5)
		scrollable_treelist.add(tree)

		self.set_border_width(1)
		self.set_size_request(1200, 350)

		col1 = Gtk.TreeViewColumn('Abbreviation', renderer, text=0) 

		col2 = Gtk.TreeViewColumn('Text', renderer, text=1)
		col2.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)

		col3 = Gtk.TreeViewColumn('Description', renderer, text=2)

		for item in [col1, col2, col3]:
			item.set_resizable(True)
			item.set_sort_column_id(0)
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
			pokeylogger.debug("\t Search window selection changed : {}".format(model[treeiter][0]))

