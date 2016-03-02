#!/usr/bin/python

from lib import *
#from lib.dedupe import *
from gi.repository import Gtk
import time, logging, getpass
import traceback
import argparse
import pokeyworks.pokeyworks as fw

#******************************GLOBALS**********************************
PURPLE_CONV_TYPE_IM=1

# HGTools Functionality
USER_SELECTION=0
	
# Create logger, default to logging.DEBUG
hgt_logger = utils.setup_logger('hgt_logger', logging.DEBUG, LOG_PATH)
	
#*****************************END LOGGING*******************************

class HGToolsApplication(object):
	
	def __init__(self):
		hgt_logger.debug('[*] Begin HGToolsApplication.__init__()')
		
		try:
			# Set up command-line argument handler
			parser = argparse.ArgumentParser()
		
			parser.add_argument("-d", "--debug", help="Enable Debugging mode",
								action="store_true")
			
			# Capture command-line arguments
			self.args = parser.parse_args()
			
			# Initialize and populate config values
			
			# File Values
			config = fw.PokeyConfig('./hgt.conf')
			# Other Values
			config.log_path = ('./tmp/{!s}.log'.format(timepart))
			config.timepart = time.strftime("%Y%m%d")
			config.env_user = getpass.getuser()
			
			# Set favicon path using the utils hgt_resource_path method
			# and the config file's relative path location
			self.favicon = utils.hgt_resource_path(config.favicon).replace('lib/','')
			
			# Initialize to empty(new) user level until DB is checked
			config.user_level = ''
			
			# Finalize Config
			self.config = config
		except:
			raise
			sys.exit(1)
		else:
			self.execute()
		finally:
			sys.exit(0)
		
	def execute(self):
		""" Executes the main application, window, and Gtk Loop """
		hgt_logger.debug('[*] Begin HGToolsApplication.execute()')
		
		try:
			# Initiate stle
			gui.gtk_style(CSS_PATH)
			
			# Instantiate Gtk window
			self.win = gui.MainWindow(ENV_USER, favicon, logging.DEBUG)
			self.win.connect("delete-event", Gtk.main_quit)
			
			# Show window
			hgt_logger.debug('[*] Showing Window')
			self.win.show_all()
			
			# Entering main_loop
			hgt_logger.debug('[*] Entering Gtk.main()')
			Gtk.main()
			
		except (KeyboardInterrupt, SystemExit):
			# Capture and exit upon sys.exit() and CTRL+C events
			hgt_logger.debug('[*] Exit command detected!')
			Gtk.main_quit()
			self.failsafe()
			
		except:
			raise
			
	def failsafe():
		""" Failsafe to close connections if open, and other cleanup """
		hgt_logger.debug('[*] Failsafe engaged!')
		
		pass
	
if __name__ == '__main__':
	HGToolsApplication()
