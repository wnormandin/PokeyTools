#!/usr/bin/env python
#***********************************************************************
#		Default logging configuration settings
#		https://docs.python.org/2/library/logging.html#logger-objects
#*******************************DEV LIST********************************

import logging, sys, os

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
	
	cons_handler = logging.StreamHandler(sys.stdout)
	cons_handler.setFormatter(cons_formatter)
	logger.addHandler(cons_handler)
	
	if level==logging.DEBUG:
		
		last_run = logging.FileHandler('./tmp/last_run.log', 'w')
		last_run.setFormatter(file_formatter)
		logger.addHandler(last_run)
	
	return logger
