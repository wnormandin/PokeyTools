#!/usr/bin/python
#**************************Domain Tools*********************************
#(DNS, Whois, SSL, Propagation)

def dmn_main():
	start=time.clock()
	clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
	url = clip.wait_for_text()
	print url
	
	flags = {}
	flags['url'] = url
	flags['urlparse'] = urlparse(url)
	flags['prop'] = ''
	flags['dns'] = ''
	
	dmn_parse(flags)
	
	if flags['pass']:
		dmn_dig(flags)
		dmn_whois(flags)
		dmn_ssl(flags)	
		dmn_prop(flags)
		return flags
	else:
		return False
	
def dmn_parse(flags):
	try:
		parts = flags['urlparse'].hostname.split('.')
	except AttributeError:
		flags['pass']=False
		parts = 'empty'
	
	if (len(parts) < 2 or len(parts) > 5):
		flags['pass']=False
		
	else:
		# Verify TLD validity
		response = urllib2.urlopen('http://data.iana.org/TLD/tlds-alpha-by-domain.txt')
		tlds = response.read()
		tlds=[tld.strip() for tld in tlds.split()]
		
		if parts[-1].upper() in tlds:
		
			if len(parts) == 2:
				flags['domain'] = '{}.{}'.format(*parts[-2:])
			else:
				if (parts[-2].upper() in tlds and parts[-3] != 'www'):
					flags['domain'] = '{}.{}.{}'.format(*parts[-3:])
				else:
					flags['domain'] = '{}.{}'.format(*parts[-2:])
			flags['pass']=True
		else:
			flags['pass']=False

def dmn_dig(flags):
	digs = ('A', 'NS', 'TXT', 'MX', 'CNAME')
	for dig in digs:
		cmd = 'timeout 3 dig {} {} +nocomments +noadditional +noauthority'.format(flags['domain'], dig)
		flags['dns']+=dmn_dig_parse(dmn_run_cmd(cmd))
	
def dmn_dig_parse(retval):
	result = ''
	for line in retval.splitlines():
		line.strip()
		if (line != '' and ';' not in line):
			result += ('{}\n'.format(line))
	result += '\n'
	return result

def dmn_whois(flags):
	cmd = 'timeout 5 whois -H {}'.format(flags['domain'])
	flags['whois'] = dmn_run_cmd(cmd).splitlines()
	
def dmn_run_cmd(cmd):
	hgt_logger.info('[*] Running command : {}'.format(cmd))
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	retval = p.communicate()[0]
	return retval
	
def dmn_ssl(flags):
	cmd = 'echo "QUIT" | timeout 5 openssl s_client -connect {}:443'.format(flags['domain'])
	cmd += ' 2>/dev/null | openssl x509 -noout -text'
	flags['ssl'] = dmn_run_cmd(cmd).splitlines()
	
def dmn_prop(flags):
	srv_list = [
	['Poland', '213.25.129.35'],
	['Indonesia',  '203.29.26.248'],
	['US', '216.218.184.19', '76.12.242.28'],
	['Australia', '203.59.9.223'],
	['Brazil', '177.135.144.210'],
	['Italy', '88.86.172.11'],
	['India',  '182.71.113.34'],
	['Nigeria', '41.58.157.70'],
	['Egypt', '41.41.107.38'],
	['UK', '109.228.25.69', '80.195.168.42'],
	['Google', '8.8.8.8']]
	
	flags['prop'] = ''
	
	for test in srv_list:
		loc = test.pop(0)
		
		if isinstance(test, (list, tuple)):
			for ip in test:
				dmn_prop_append(flags, loc, ip)
		else:
			dmn_prop_append(flags, loc, test)
			
		print flags['prop']

def dmn_prop_append(flags, loc, ip):
	cmd = ('dig @{} {} +short'.format(ip, flags['domain']))
	flags['prop'] += '\n{} : {} Result\n'.format(loc, ip)
	print cmd
	flags['prop'] += dmn_dig_parse(dmn_run_cmd(cmd))
