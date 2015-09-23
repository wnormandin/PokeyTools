#!/usr/bin/env python
#
# String de-duplication library
#
# ** Tweaks
#
#		For longer scripts, you may want to separate them into a 
#		second import file, and tweak the settings to look only at
#		the dd_commonchars, dd_ratio, and dd_lev tests to handle potential
#		syntax variations.  
#
# Usage :
#
#		1. Call dd_match(arg1, arg2, [tests, params]) :
#
#				a. arg1 	= The smaller list to be compared
#				b. arg2 	= The larger list to be compared
#				c. tests	= Optional list of tests to be run, named by
#							  function (dd_lev, dd_jaro, dd_jarwink, etc)
#							  Default=TESTS
#				d. params	= Optional list of parameters for the corre-
#							  sponding tests list above.  Default=PARAMS
#
#		2. Return format :
#
#				((idx1, val1, idx2, val2, score, time), ...)
#
#				a. idx1		= The row number of val1 in arg1
#				b. val1		= The value compared from arg1
#				c. idx2		= The row number of val2 in arg2
#				d. val2		= The value compared from arg2
#				e. score	= The dd_distance_heuristic score for this
#							  comparison
#				f. time		= Execution time for this comparison
#
#*******************************DEV LIST********************************
#
#	Add to Readme
#
#*****************************END DEV LIST******************************

#***********************************************************************
#            														   *
#							CONFIGURATION							   *
#																	   *
#***********************************************************************

from log import *
import logging
import difflib, sys, time, os
import multiprocessing

#***************************MULTIPROCESSING*****************************
#		Set the MULTI_PROC variable to False below to turn off
#		parallel processing. 

MULTI_PROC=False
MAX_PROC=5
matchlist = list()
	
#********************************TESTS**********************************
# Set the tests to be run by the dd_runall function.  When adding
# tests to the list, be sure to add a corresponding paramter below.

TESTS = []		
# Tests (*=core)
TESTS.append('dd_ratio')			#*Include difflib Similarity Ratio
TESTS.append('dd_jaro')				#*Include Jaro Distance
TESTS.append('dd_jarwink')			#*Include Jaro-Winkler Distance
TESTS.append('dd_lev')				#*Include Levenshtein Distance (Slow)
#TESTS.append('dd_hamming')			# Include Hamming Distance
#TESTS.append('dd_transpositions')	# Include Transpositions
#TESTS.append('dd_commonchars')		# Include Common Characters

# SCORE PARAMETERS
# PARAMS : [(threshold, weight), ....]

# PARAMS = [(.9,.2),(.9,.25),(.9,.25),(3,.3)]	# Strict settings, less matches
PARAMS = [(.8,.2),(.8,.25),(.8,.25),(4,.3)]	# Moderate settings
# PARAMS = [(.7,.2),(.7,.25),(.7,.25),(5,.3)]	# Relaxed settings, more matches

# PARAMS stores the thresholds and weights for each core test which 
# dictate what is considered a probable match.

# These values will correspond to the order of the core tests
# identified above.  If a test is missing a related parameter
# set, it will default to (0, 0)

# dd_distance_heuristic match score threshold (lower = more matches)(<=1)
SCORE_THRESHOLD = .25

#***********************ALGORITHM PARAMETERS****************************

# JARO_WINKLER
PREFIX_MAX = 4					# Maximum prefix bonus multiplier
PREFIX_VAL = 0.1				# Adjust for more/less bonus (max .25)
BOOST_THRESH = 0.7				# Boost threshold (vs Jaro Distance)

# COMMON_CHARACTERS
ABS_MIN = 0						# Absolute minimum string position 

# dd_runall and dd_match table column headers
COL_HEADERS = ['TEST FUNCTION', 'RESULT', 'TIME(s)']

#******************************END CONFIG*******************************

#*******************************LOGGING*********************************

# Set to False to turn off logging
LOGGING = True

# Set to True to increase verbosity
DEBUG = True

# Log File Path, defaults to /<script_dir>/tmp/<datetime>,log
timepart = time.strftime("%Y%m%d")
LOG_PATH = os.path.dirname(__file__) + ('/tmp/%s.log' %  str(timepart))
LOG_PATH = LOG_PATH.replace(__file__, '')

def log_init(file_loc=LOG_PATH, opt_dbg=False):
	
	if not LOGGING:
		level=logging.CRITICAL
	elif opt_dbg or DEBUG:
		level=logging.DEBUG
	else:
		level=logging.INFO
	
	#Check for existing loggers/get new loggers
	if not logging.Logger.manager.loggerDict:
		dd_logger=setup_logger(__name__, level, file_loc)
	elif 'hgtools.py' in logging.Logger.manager.loggerDict.keys():
		dd_logger=logging.getLogger('hgtools.py')
	else:
		dd_logger=setup_logger(__name__, level, file_loc)
		
	return dd_logger
	
dd_logger=log_init(LOG_PATH, DEBUG)
	
#*****************************END LOGGING*******************************


#********************************dd_test********************************
#
#		Test function for debugging

def dd_test():

	stats=[]
	
	#Edit these lists to test comparisons
	arg1=('MARK', 'DAVID', 'HAROLD', 'CHARLES', 'MARCUS')
	arg2=('FRED', 'DAVE', 'HARRY', 'CHARLIE', 'MARCOS', 'MARC', 'LESLIE')

	returned, stats = dd_match(arg1, arg2, 0.95)
	
	for row in returned:
		dd_logger.debug(row)
		
	return returned, stats

#******************************END dd_test******************************
	
#*******************************dd_match*******************************
#
#		Primary match algorithm 	

def dd_match(arg1, arg2, match_thresh=0.95):

	start = time.clock()

	dd_logger.debug('Preparing for run...')
	checkglobals(arg1, arg2)
		
	# Returns a list of potential matches, with scores
	# Compares each value in the list 'arg1' and checks
	# against every record in the list 'arg2'.  Can be
	# slow with larger datasets
		
	dd_logger.debug('Begin string comparisons')
	
	try:
		if not MULTI_PROC:
			
			collect_results(match_process(arg1, arg2, match_thresh))
			
		else:
			while i in range(len(arg1)):
				
				this_min = min(5*MAX_PROC, len(arg1)-i)
				pool = Pool(processes=this_min)
				chunk = arg1[i:i+this_min]
				
				# nibble = (arg1=(10 rec), arg2, match_thresh)
				for nibble in chunk:
					pool.apply_async(match_process, args=(nibble),
									callback=collect_results)
									
				pool.close()
				pool.join()
				
				i += MAX_PROC*5

	except Exception as e:
		dd_logger.error("{0} : \n{1!r}".format(sys.exc_info()[0].__name__ , e.args))
		if DEBUG:
			raise
	
	else:
		stats=[]
		stats.append(str(len(arg1)*len(arg2)))
		stats.append(str(len(matchlist) if matchlist != None else None))
		stats.append(str(time.clock()-start) + 's')
		
	return matchlist, stats
		
#******************************END dd_match*****************************

#***********************************************************************
#            														   *
#								ALGORITHMS							   *
#																	   *
#***********************************************************************

#*******************************dd_runall*******************************
#
#		Executes each algorithm and returns a list with the results
#		If no tests list is provided, the default list configured in
#		the GLOBALS area will be used.	
#
#  http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies

def dd_runall(arg1, arg2, tests=TESTS):
	
	start=time.clock()
	start2=time.clock()
	results = []
	
	dd_logger.debug('Running Tests')
	print_lengths(arg1, arg2)
	
	for i in range(len(tests)):
			
		start2=time.clock()
		tst = globals()[tests[i]](arg1, arg2)
		end = time.clock()
		
		results.append((tst, end-start2))
			
	print_table(tests, results)
	dd_logger.debug('Run time : %ss' % str(end-start))
			
	return results
		
#*******************************dd_hamming******************************
#
#		Calculates the Hamming distance between two strings.
#
#		https://en.wikipedia.org/wiki/Hamming_distance

def dd_hamming(arg1, arg2):
	
	# Hamming distance is undefined for unequal-length strings
	if len(arg1)!=len(arg2):
		retval=None	
	
	else:
		retval=sum(ch1 != ch2 for ch1, ch2 in zip(arg1, arg2))
	
	dd_logger.debug('Hamming Distance : %s' % str(retval))
	return retval
	
#*********************************dd_lev********************************
#
#		Calculates the Levenshtein distance between two strings 
#
#		https://en.wikipedia.org/wiki/Levenshtein_distance

def dd_lev(arg1, arg2):

	if len(arg1) > len(arg2):
		arg1,arg2 = arg2,arg1
        
	distances = range(len(arg1) + 1)
    
	for index2,char2 in enumerate(arg2):
		newDistances = [index2+1]
        
		for index1,char1 in enumerate(arg1):

			if char1 == char2:
				newDistances.append(distances[index1])

			else:
				newDistances.append(1 + min((distances[index1],
											distances[index1+1],
											newDistances[-1])))
		distances = newDistances
		
	dd_logger.debug('Levenshtein Distance : %s' % str(distances[-1]))	
	return distances[-1]
		
#*******************************END dd_lev******************************
			
#*******************************dd_jarwink******************************
#
#		Calculates the Jaro-Winkler Distance of the two passed strings
#
#		https://en.wikipedia.org/wiki/Jaro-Winkler_distance

def dd_jarwink(arg1, arg2):
	
	start = time.clock()
	prefix_len = dd_jw_prefix(arg1, arg2)
	
	dd_logger.debug('Calculating Jaro-Winkler Distance')
	dd_logger.debug('	Constants')
	dd_logger.debug('	PREFIX_MAX		=	%s' % str(PREFIX_MAX))
	dd_logger.debug('	PREFIX_VAL		=	%s' % str(PREFIX_VAL))
	dd_logger.debug('	BOOST_THRESH		=	%s' % str(BOOST_THRESH))
	dd_logger.debug('	prefix_len		=	%s' % str(prefix_len))
	
	# First Calculate the Jaro Distance
	jaro_dist = dd_jaro(arg1, arg2)
	
	dd_logger.debug('Jaro Distance : %s' % str(jaro_dist))
		
	# Check for bonus criteria :
	#
	# Set the PREFIX_LEN to 0 to apply the bonus to all comparisons
	# where the Jaro Distance is greater than the Boost Threshold
	# stored in the global variable BOOST_THRESH
	
	if (prefix_len<=0 and jaro_dist > BOOST_THRESH):
		
		bonus = PREFIX_VAL*(1-jaro_dist)
		
		dd_logger.debug('Winkler Bonus : %s' % str(bonus))
		retval = jaro_dist + bonus
	
	# If PREFIX_LEN is set to any value above 0, the bonus will only
	# be applied if the first N characters (where N = PREFIX_LEN) are
	# identical in both strings AND the Jaro Distance is greater than 
	# the Boost Threshold stored in the global variable BOOST_THRESH
	
	elif (arg1[:prefix_len-1]==arg2[:prefix_len-1] and jaro_dist > BOOST_THRESH):
		
		bonus = (prefix_len*PREFIX_VAL)*(1-jaro_dist)
		
		dd_logger.debug('Winkler Bonus : %s' % str(bonus))
		retval = jaro_dist + bonus
	
	# For all other cases, the return value is simply the Jaro Distance
	
	else:
		
		dd_logger.debug('No Winkler Bonus')
		
		retval = jaro_dist
	
	dd_logger.debug('Jaro-Winkler : %s' % str(retval))
				
	return retval
	
#*****************************END dd_jarwink****************************

#********************************dd_jaro********************************
#
#		Calculates the Jaro Distance of the two passed strings

def dd_jaro(arg1, arg2):
		
	m = dd_commonchars(arg1, arg2)
	t = dd_transpositions(arg1, arg2)
	
	if m==0:
		retval = 0
		
	else:
			
		factor1 = float(m) / len(arg1)
		factor2 = float(m) / len(arg2)
		factor3 = float(m-t) / m
		
		retval = (factor1 + factor2 + factor3) / 3

	return retval

#******************************END dd_jaro******************************

#***********************dd_distance_heuristic***************************
#
#		Calculates the heuristic score of the results for a match
#		based on the parameters set in the global PARAMS

def dd_distance_heuristic(results, tests=TESTS, params=PARAMS):
	
	composite=0
	
	for i in range(len(tests)):
		
		try:
			if tests[i]=='dd_lev':
				if results[i][0]<=params[i][0]:
					composite += params[i][1]
			elif results[i][0]>1:
				dd_logger.info('distance adjustment : %s' % str(results[i][0]))
				dd_logger.info('adjusted to : %s' % str(1-(results[i][0]-1)))
				if (1-(results[i][0]-1)<=params[i][0]):
					composite += params[i][1]
			elif results[i][0]<0:
				pass
			else:
				composite += (results[i][0]*params[i][1])
				
		except Exception as e:
			if i>len(params):
				sys.exc_clear()
				pass
			else:
				err= "{0} -:- \n{1!r}"
				dd_logger.error(err.format(sys.exc_info()[0].__name__ , e.args))
				
	dd_logger.debug('Distance Heuristic : %s' % str(composite))
	return composite

#*******************************dd_ratio********************************
#
#		Calculates the difflib.SequenceMatcher similarity ratio

def dd_ratio(arg1, arg2):
	
	sqm = difflib.SequenceMatcher
		
	retval = sqm(None, arg1, arg2).ratio()
	
	dd_logger.debug('difflib Similarity Ratio : %s' % str(retval))
		
	return retval
		
#******************************END dd_ratio******************************
	
#***********************************************************************
#            														   *
#								FUNCTIONS							   *
#																	   *
#***********************************************************************

# Score checking
def pass_score(score, match_thresh):
	ret_val=False
	
	if score >= SCORE_THRESHOLD:
		if score >= match_thresh:
			ret_val=True
			
	return ret_val
	
# Calculation of letter transpositions
def dd_transpositions(arg1, arg2):
		
	transposition = 0.0
	
	if len(arg1) > len(arg2):
		tmp=arg1
		arg1=arg2
		arg2=tmp
	
	for i in range(len(arg1)-1):
		
		for j in range(len(arg2)-1):
			
			if (i==j and arg1[i]==arg2[j]):
				pass
			
			elif (i==j and arg1[i]!=arg2[j]):
				
				if ((j-1) >= 0 and (i-1) >= 0):
					
					if (((i+1) <= len(arg1)) and ((j+1) <= len(arg2))):

						if (arg1[i]==arg2[j-1] and arg1[i-1]==arg2[j]):
							transposition += 1
				
						elif (arg1[i]==arg2[j+1] and arg1[i+1]==arg2[j]):
							transposition += 1
	
	transposition = transposition / 2
	
	dd_logger.debug('Transpositions : %s' % str(transposition))
		
	return transposition

# Calculation of Common Characters
def dd_commonchars(arg1, arg2):
				
	len1 = int(len(arg1))
	len2 = int(len(arg2))
	com = 0 # Common Characters count
	
	max_dist = max(len1, len2)
	max_dist = max_dist/2
	max_dist = max_dist - 1

	for c in range(0, len1):
		
		min_cmp=c+max_dist
		max_cmp=c-max_dist
		
		for i in range(max(max_cmp, ABS_MIN), min(len2, min_cmp)):
			
			if arg1[c]==arg2[i]:
				
				com += 1
				
	dd_logger.debug('Common Characters : %s' % str(com))

	return com

# Jaro-Winkler prefix bonus multiplier calculation
def dd_jw_prefix(arg1, arg2):
	
	match_list = []
	retval = 0

	for i in range(PREFIX_MAX):
		
		if arg1[i]==arg2[i]:
			match_list.append(arg1[i])
			retval += 1
	
		else:
			break
			
	dd_logger.debug('Prefix matches : %s' % ''.join(match_list))		
	dd_logger.debug('prefix_len : %s' % str(retval))
	
	return retval
	
# Prints the strings and their lengths
def print_lengths(arg1, arg2):

	dd_logger.debug('STRING_1 	: %s' % arg1)
	dd_logger.debug('LENGTH	: %s' % str(len(arg1)))
	dd_logger.debug('STRING_2	: %s' % arg2)
	dd_logger.debug('LENGTH	: %s' % str(len(arg2))	)

# Tabular print function for dd_runall, dd_match
def print_table(labels, values):
	
	col_width = max(max_width(labels), max_width(values), max_width(COL_HEADERS))
	
	dd_logger.debug('Generating Table')
	dd_logger.debug('Max column width : %s' % str(col_width+1))
	
	line=''	
	for c in COL_HEADERS:
		line += '| {{0: <{}}}'.format(col_width).format(c) + ' '
		
	dd_logger.debug(line)
		
	for t, r in zip(labels, values):
		line = '| {{0: <{}}}'.format(col_width).format(t) + ' '
		line += '| {{0: <{}}}'.format(col_width).format(r[0])+ ' '
		line += '| {{0: <{}}}'.format(col_width).format(r[1]) + 's |'
		
		dd_logger.debug(line)

# Calculate the maximum length of the strings in the passed list
# Iterates through nested lists using recursion
def max_width(values):
	
	m = []
	
	for v in values:
		
		if type(v)=='list':
				m.append(max_width(v))
				
		else:
			m.append(len(v))
		
	return max(m)+1
	
# Multiprocessing result collection function
def collect_results(result):
	matchlist.extend(result)
	
def match_process(arg1, arg2, match_thresh):
	
	if MULTI_PROC:
		dd_logger.debug("PID %s spawned, parent PID %s" % (os.getpid(), os.getppid()))
		
	result = list()
	for row1 in arg1:
		for row2 in arg2:
			
			row2 = row2.strip()	
			start2 = time.clock()
			score = dd_distance_heuristic(dd_runall(row1, row2))
			result.append((pass_score(score, match_thresh), 
								arg1.index(row1), row1, 
								arg2.index(row2), row2, 
								'%(s)0f' % {"s": score},
								'%(t)0F' % {"t": time.clock()-start2}))
	return result
	
#*****************************checkglobals******************************
#
#		Checks the global constants for adherence to the parameters
#		described below for each algorithm.  Alter at your peril.	
def checkglobals(arg1, arg2):
	
	global PREFIX_MAX
	global PREFIX_VAL
	global BOOST_THRESH
	global ABS_MIN
	
	# JARO_WINKLER
	
	# The Prefix Maximum cannot be less than 1
	# Check for negative values before int type	
	if PREFIX_MAX < 1:
		dd_logger.warning('Invalid PREFIX_MAX : %s' % str(PREFIX_MAX))
		PREFIX_MAX = 1
		dd_logger.warning('Set to : %s' % str(PREFIX_MAX))
	
	# The Prefix Maximum cannot be greater than 4
	if PREFIX_MAX < 0:
		dd_logger.warning('Invalid PREFIX_MAX : %s' % str(PREFIX_MAX))
		PREFIX_MAX = 0
		dd_logger.warning('Set to : %s' % str(PREFIX_MAX))
	
	# The Prefix Value (bonus weight) must be 0.01 or above
	if PREFIX_VAL < 0.01:
		dd_logger.warning('Invalid PREFIX_VAL : %s' % str(PREFIX_VAL))
		PREFIX_VAL = 1
		dd_logger.warning('Set to : %s' % str(PREFIX_VAL))
		
	# The Prefix Value (bonus weight) must be 0.25 or below
	if PREFIX_VAL > 0.25:
		dd_logger.warning('Invalid PREFIX_VAL : %s' % str(PREFIX_VAL))
		PREFIX_VAL = 0.25
		dd_logger.warning('Set to : %s' % str(PREFIX_VAL))
	
	# The Boost Threshold must be 0.1 or above	
	if BOOST_THRESH < 0.1:
		dd_logger.warning('Invalid BOOST_THRESH : %s' % str(BOOST_THRESH))
		BOOST_THRESH = 0.1
		dd_logger.warning('Set to : %s' % str(BOOST_THRESH))
		
	# The Boost Threshold must be less than / equal to 0.9	
	if BOOST_THRESH > 0.9:
		dd_logger.warning('Invalid BOOST_THRESH : %s' % str(BOOST_THRESH))
		BOOST_THRESH = 0.9
		dd_logger.warning('Set to : %s' % str(BOOST_THRESH))
	
	# COMMON_CHARACTERS
		
	# The Absolute Minimum Position must be greater than / equal to 0	
	if ABS_MIN < 0:
		dd_logger.warning('Invalid ABS_MIN : %s' % str(ABS_MIN))
		ABS_MIN = 0
		dd_logger.warning('Set to : %s' % str(ABS_MIN))
		
	# The Absolute Minimum Position must be less than / equal to 3
	if ABS_MIN > 3:
		dd_logger.warning('Invalid ABS_MIN : %s' % str(ABS_MIN))
		ABS_MIN = 3
		dd_logger.warning('Set to : %s' % str(ABS_MIN))
	
#***************************END checkglobals****************************

