#!/usr/bin/python

from lib import *
#from lib.dedupe import *
from gi.repository import Gtk
import time, logging, getpass
import traceback
import argparse
import sys
import pokeyworks as fw


#******************************GLOBALS**********************************
PURPLE_CONV_TYPE_IM=1

# HGTools Functionality
USER_SELECTION=0
LOG_PATH = 'tmp/pokeytools.log'

# Create logger, default to logging.DEBUG
pokeylogger = fw.setup_logger('pokeylogger', logging.DEBUG, LOG_PATH)

#*****************************END LOGGING*******************************

class HGToolsApplication(object):

	def __init__(self):
		pokeylogger.debug('[*] Begin HGToolsApplication.__init__()')

		try:
			# Set up command-line argument handler
			parser = argparse.ArgumentParser()

			parser.add_argument("-d", "--debug", help="Enable Debugging mode",
								action="store_true")

			# Capture command-line arguments
			self.args = parser.parse_args()

			# Initialize and populate config values

			# File Values
			config = fw.PokeyConfig('./application.conf')
			# Other Values
			config.timepart = time.strftime("%Y%m%d")
			config.log_path = ('./tmp/{!s}.log'.format(config.timepart))
			config.env_user = getpass.getuser()

			# Set favicon path using the utils hgt_resource_path method
			# and the config file's relative path location
			self.favicon = fw.resource_path(__file__,config.favicon[0])

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
		pokeylogger.debug('[*] Begin HGToolsApplication.execute()')

		try:
			# Initiate stle
			gui.gtk_style(self.config.css_path[0])

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
	HGToolsApplication()
