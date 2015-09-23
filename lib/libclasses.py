#!/usr/bin/env python

from libfunctions import *
from gi.repository import Gtk
import sys, logging
import log # Must add if not in __init__.py

#*******************************LOGGING*********************************

hgt_logger=logging.getLogger('hgtools.py')
	
#*****************************END LOGGING*******************************
		
class gtk_show_window(Gtk.Window):
	
	def __init__(self, liststore):
	
		Gtk.Window.__init__(self, title="HGTools Selection Window")
		hgt_logger.debug("HGTools selection window spawned")
		hgt_logger.debug("Building grid")
		self.set_border_width(20)
		self.grid = Gtk.Grid()
		self.grid.set_column_homogeneous(True)
		self.grid.set_row_homogeneous(True)
		self.add(self.grid)
		
		self.liststore = liststore
		self.treeview = Gtk.TreeView.new_with_model(self.liststore)
		
		hgt_logger.debug("Attaching columns")
		for i, column_title in enumerate(["qCode", "Tool Text", "Description"]):
			renderer = Gtk.CellRendererText()
			renderer.props.wrap_width=600

			column = Gtk.TreeViewColumn(column_title, renderer, text=i)
			column.set_sort_column_id(i)
			self.treeview.append_column(column)
			
		select = self.treeview.get_selection()
		select.connect("changed", self.on_tree_selection_changed)
		
		self.buttons=list()
		hgt_logger.debug("Attaching buttons")
		for button_text in ["Cancel", "Select"]:
			button = Gtk.Button(button_text)
			self.buttons.append(button)
			button.connect("clicked", self.on_selection_button_clicked)
		
		self.scrollable_treelist = Gtk.ScrolledWindow()
		self.scrollable_treelist.set_vexpand(True)
		
		hgt_logger.debug("Attaching labels")
		label = Gtk.Label("Selection : ")
		
		self.selection_label = label
		
		self.grid.attach(self.scrollable_treelist, 0, 1, 10, 10)
		self.grid.attach_next_to(self.buttons[0], self.scrollable_treelist, 
								Gtk.PositionType.BOTTOM, 1, 1)
		
		for i, button in enumerate(self.buttons[1:]):
			self.grid.attach_next_to(button, self.buttons[i], 
								Gtk.PositionType.RIGHT, 1, 1)
		
		self.grid.attach(self.selection_label, 0, 0, 1, 1)
		
		hgt_logger.debug("Grid complete, showing window")
								
		self.scrollable_treelist.add(self.treeview)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.show_all()
		
	def on_selection_button_clicked(self, widget):
		
		button_selection = widget.get_label()
		hgt_logger.debug("Button clicked : %s" % button_selection)
		
		if button_selection=="Cancel":
			while Gtk.events_pending():
				Gtk.main_iteration()
			Gtk.main_quit()
			sys.exit(3)
			
		if button_selection=="Select":
			while Gtk.events_pending():
				Gtk.main_iteration(False)
				
			Gtk.main_quit()
		
	def on_tree_selection_changed(self, selection):
		
		model, treeiter = selection.get_selected()
    
		if treeiter != None:
			
			self.selected = model[treeiter][0]
			self.selection_label.set_label("Selection : " + self.selected)
			hgt_logger.debug("Selection changed : %s" % self.selected)

# Class to allow users to select from a list of potential matches, 
# matches with a score above the match_thresh will be auto-selected.
			
class gtk_dedupe_selections(Gtk.Window):
	
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
