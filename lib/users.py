#!/usr/bin/python
#************************User Functions*********************************
# Functions to grant admin permissions to some users
import dbsearch

def user_main(user):
	
	first_flag, u_lvl = user_first_logon(user)
	if first_flag:
		hgt_logger.info('[*] First user logon detected : {}'.format(user))
		user_db_add(user)
		sys_create_alias()
	msg = 'hgtools_gtk accessed'
	user_db_log(msg, user)
	hgt_logger.debug('\t User Permission Level : {}'.format(u_lvl))
	return u_lvl
		
def user_first_logon(user):
	
	str_sql = 'SELECT user_level FROM hgtools_users '
	str_sql += 'WHERE user_ldap="{}"'.format(user)
	result = dbsearch.hgt_query(str_sql)
	
	try:
		hgt_logger.debug('\t User found! Access : {}'.format(result.strip('\n')))
		return False, result.strip('\n')
	except:
		return True, 'USER'
	
def user_db_add(user):
	str_sql = 'INSERT INTO hgtools_users (user_ldap, user_level, user_group) '
	str_sql += 'VALUES ("{}", "{}", "{}");'.format(user, 'USER', 'NEW_USERS')
	hgt_query(str_sql)
	hgt_logger.info('[*] User {} added to hgtools_users'.format(user))
	
def user_db_log(msg, user):
	str_sql = 'INSERT INTO hgtools_log (log_type, log_text) '
	str_sql += 'VALUES ("{}", "{}");'.format(user, msg)
	hgt_query(str_sql) 
	hgt_logger.info('[*] DB Log Record Created > hgtools_log')

#************************/User Functions******************************** 
