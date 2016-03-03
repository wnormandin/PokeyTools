#!/usr/bin/python
#************************User Functions*********************************
# Functions to grant admin permissions to some users
import dbsearch
import logging

def user_main(user):
	
	pokeylogger = logging.getLogger('pokeylogger')
	
	first_flag, u_lvl = user_first_logon(user)
	if first_flag:
		pokeylogger.info('[*] First user logon detected : {}'.format(user))
		user_db_add(user)
	msg = 'hgtools_gtk accessed'
	user_db_log(msg, user)
	pokeylogger.debug('\t User Permission Level : {}'.format(u_lvl))
	return u_lvl
		
def user_first_logon(user):
	
	pokeylogger = logging.getLogger('pokeylogger')
	
	str_sql = 'SELECT user_level FROM hgtools_users '
	str_sql += 'WHERE user_ldap="{}"'.format(user)
	result = dbsearch.hgt_query(str_sql)
	
	try:
		pokeylogger.debug('\t User found! Access : {}'.format(result.strip('\n')))
		return False, result.strip('\n')
	except:
		return True, 'USER'
	
def user_db_add(user):
	
	pokeylogger = logging.getLogger('pokeylogger')
	str_sql = 'INSERT INTO hgtools_users (user_ldap, user_level, user_group) '
	str_sql += 'VALUES ("{}", "{}", "{}");'.format(user, 'USER', 'NEW_USERS')
	dbsearch.hgt_query(str_sql)
	pokeylogger.info('[*] User {} added to hgtools_users'.format(user))
	
def user_db_log(msg, user):
	
	pokeylogger = logging.getLogger('pokeylogger')
	str_sql = 'INSERT INTO hgtools_log (log_type, log_text) '
	str_sql += 'VALUES ("{}", "{}");'.format(user, msg)
	dbsearch.hgt_query(str_sql) 
	pokeylogger.info('[*] DB Log Record Created > hgtools_log')

#************************/User Functions******************************** 
