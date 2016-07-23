#!/usr/bin/python2.7
#-*- coding: utf-8 -*-

from lib import *
#from lib.dedupe import *
from gi.repository import Gtk
import time, logging, getpass
import traceback
import argparse
import sys, os

import pokeyworks.pokeyworks as pokeyworks

#******************************GLOBALS**********************************
PURPLE_CONV_TYPE_IM=1

# HGTools Functionality
USER_SELECTION=0
LOG_PATH = './tmp/pokeytools.log'

try:
    os.stat(LOG_PATH)
except OSError:
    with open(LOG_PATH,'a'):
        pass

# Create logger, default to logging.DEBUG
pokeylogger = pokeyworks.setup_logger('pokeylogger', logging.DEBUG, LOG_PATH)

#*****************************END LOGGING*******************************

class AdminToolsApplication(object):

	def __init__(self):
		pokeylogger.debug('[*] Begin AdminToolsApplication.__init__()')

		try:
			# Set up command-line argument handler
			parser = argparse.ArgumentParser()

			parser.add_argument("-d", "--debug", help="Enable Debugging mode",
								action="store_true")

			# Capture command-line arguments
			self.args = parser.parse_args()

			# Initialize and populate config values

			# The application.cfg file must be a PokeyConfig Base64-encoded JSON
			# file in the current implementation, need to allow for more flexible
			# configuration, see issue https://github.com/wnormandin/pokeytools/issues/8
			config = pokeyworks.PokeyConfig('./application.json',pokeyworks.PokeyConfig.json,True)
			# Other Values
			config.timepart = time.strftime("%Y%m%d")
			config.log_path = (LOG_PATH)
			config.env_user = getpass.getuser()

			# Set favicon path using the utils hgt_resource_path method
			# and the config file's relative path location
			self.favicon = pokeyworks.resource_path(__file__,config.favicon)

			# Initialize to empty(new) user level until DB is checked
			config.user_level = ''

			# Finalize Config
			self.config = config
		except:
			raise
			utils.application_exit
		else:
			self.execute()
			utils.application_exit

	def execute(self):
		""" Executes the main application, window, and Gtk Loop """
		pokeylogger.debug('[*] Begin AdminToolsApplication.execute()')

		try:
			# Initiate stle
			gui.gtk_style(self.config.css_path)

			# Instantiate Gtk window
			self.win = gui.MainWindow(
									self.config.env_user,
									self.favicon, 
									logging.DEBUG
									)

			self.win.connect("delete-event", Gtk.main_quit)

			# Show window
			pokeylogger.debug('[*] Showing Window')
			self.win.show_all()

			# Entering main_loop
			pokeylogger.debug('[*] Entering Gtk.main()')
			Gtk.main()

		except (KeyboardInterrupt, SystemExit):
			# Capture and exit upon sys.exit() and CTRL+C events
			pokeylogger.debug('[*] Exit command detected!')
			Gtk.main_quit()
			self.failsafe()

		except:
			raise

	def failsafe():
		""" Failsafe to close connections if open, and other cleanup """
		pokeylogger.debug('[*] Failsafe engaged!')

		pass

if __name__ == '__main__':
	AdminToolsApplication()
