import logging
import sys
import json

import math

from pyzabbix import ZabbixAPI, ZabbixAPIException
from datetime import datetime 

ZABBIX_URL 		  = 'http://????.com/'
SUPERDUPER_ADMIN  = 'admin'
SUPERDUPER_PASSWD = 'admin'

def zabbix_connect(self):

	try:
		zabbix = ZabbixAPI(server=self.zabbix_url)
		zabbix.login(
			user=self.username, password=self.password
		)
		return zabbix
	
	except ZabbixAPIException as oO:
		print(oO)
		return None

class ZabbixAdapter(object):

	def __init__(self, zObject):

		self.zabbix_api = zObject
		self.__logger = logging.getLogger(__name__)

	def format_size(self, size):
		strsize = '0B'
		size = float(size)
		size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
		i = int(math.floor(math.log(size,1024)))
		p = math.pow(1024,i)
		s = round(size/p,2)
		return '%s%s' % (s,size_name[i]) if s > 0 else strsize

	def item_get(self, host_id=0, filters=""):
		
		method = "item.get"		
		params = {
			"output": "extend",
			#"hostid": host_id if host_id else "",
	        #"search": {
	        #    "key_": filters if filters else ""
	        #},
	        "sortfield": "key_"
		}
		if host_id:
			params['hostid'] = host_id
		if filters:
			params['search'] = {"key_": filters}

		return self.zabbix_api.do_request(
			method, params
		)

	def graph_data(self):
		
		method = "graph.get"
		params = {
			"output": "extend", "sortfield": "name"
		}
		return self.zabbix_api.do_request(
			method, params
			)
	
	def event_data(self):

		method = "event.get"
		params = {
			"output": "extend",
			#"select_acknowledges": "extend",
			#"objectids": "13926",
			#"sortfield": ["clock", "eventid"],
			#"sortorder": "DESC"
	    }
		return self.zabbix_api.do_request(
			method, params
			)

	def history_data(self):
		
		method = 'history.get'
		params = {
			"output": "extend",
        	"sortfield": "clock",
        	"sortorder": "DESC",
        	#"limit": 10
		}

		return self.zabbix_api.do_request(
			method, params
		)

	def host_get(self):

		method = "host.get"
		params = {
			#"output": ["host", "groups", "items", "name", "status"],
			#"output": ["host", "groups", "name", "status"],
			"output": "extend",
			"selectGroups": ["groupids"],

			##"selectItems": ["error", "lastclock", "status", "hostid" "name", "lastvalue", "lastns"],
			##"limit": 5
			
			##--- wrong ---
			#"filter": {
			#	"groupid": "8"
			#}

			##--- right ---
			#"groupid": [8]
		}
			
		return self.zabbix_api.do_request(method, params)
		
	def host_group(self, groupid=0):

		method = "hostgroup.get"
		params = {
			"output": ["host", "groups", "items", "name", "status"],
			#"filter": {
			#	"groupid": groupid if groupid else ""
			#}

			##"output": ["host", "groups", "name", "status"],
			"selectGroups": ["groupids"],
			##"selectItems": ["error", "lastclock", "status", "hostid" "name", "lastvalue", "lastns"],
			##"limit": 5
		}
			
		return self.zabbix_api.do_request(method, params)

	def discover_host(self, hostid=0):

		method = "dservice.exists"
		params = {
			"output": "extend",
			#"druleids": "4"
        	#"selectDServices": "extend",
			#"filter": {
			#	"dhostid": hostid if hostid else ""
			#}
		}
			
		return self.zabbix_api.do_request(method, params)

	def system_status(self):

		self.__logger.error('***')
		method = "item.get"
		params = {
			'output': 'extend',
			'sortfield': 'name'
		}
		issues = self.zabbix_api.do_request(method, params)
		return issues

	def trigger_get(self):
		method = "trigger.get"
		params = {
		#	'only_true':1,
		#	'skipDependent':1,
			'monitored':1,
			'active':1,
			'output':'extend',
			'expandDescription':1,
			'expandData':'host',
			'sortfield':'priority',
        	'sortorder':'DESC',
         	'filter':{
        		"status": 0 #, "priority": ['4','5']
        	}
		}
		
		return self.zabbix_api.do_request(
			method, params
			)
		
	def screen_data(self):

		method = 'screen.get'
		params = {
			"selectScreenItems": "extend", 
			"output" : "extend"
		}

		return self.zabbix_api.do_request(
			method, params
		)

	def web_monitoring(self): pass

	def favorites(self): pass
	
	def httptest(self):
		method = "httptest.get"		
		params = {
			"output": "extend",
	        "selectSteps": "extend",
	        "httptestids": "1",
	        #"sortfield": "httptestid"
		}

		return self.zabbix_api.do_request(
			method, params
		)

class Zabbix_Account(object):

	def __init__(self, zObject):

		self.zabbix_api = zObject

	def is_user_exist(self, usr):

		""" Checks if User Exist. Returns boolean"""
		userExist = False
		if self.zabbix_api.user.get(search={'alias':usr}): 
			userExist = True

		return userExist

	def get_all_users(self):
		"Returns all users"
		return self.zabbix_api.user.get(output="extend")

	def get_user_info(self, user, need):
		""" Accepts user's alias and asking return data. """
		a = self.zabbix_api.user.get(search={'alias':user}, output='extend')
		for x in a: return x[need] 
		
	def create_user(self, user, passwd, usrgroup=[], media=[]):
	
		""" Accepts Dictionary. Returns boolean. 
			Parameters: alias, passwd, usrgrps(list), media(list) - Required
				name, surname - Not Required

			media = {'sendto': '1@e.com', 'mediatypeid': '1'}, {'sendto': '1@e.com', 'mediatypeid': '2'}

			For other params: 
				https://www.zabbix.com/documentation/2.4/manual/api/reference/user/object 

			*** NEXT: SHOULD ACCEPT NAME, LASTNAME AS PARAMS ***
		"""
		
		try: 
			if self.is_user_exist(user): return False

			usrgrp = self.set_user_roup(usrgroup)
			self.zabbix_api.user.create(
				alias=user, passwd=passwd, usrgrps=usrgrp, user_medias=media
				)
			return "%s successfully added as user"%user

		except ZabbixAPIException as oO:
			print (traceback.print_exc())
			return "Something went wrong. Contact Administrator"

	def set_user_roup(self, grp=[]):
		""" Accepts List as Parameter. Returns Dictionary of usergroupids """

		for grpName in grp:
			if self.zabbix_api.usergroup.exists(name=grpName):
				return {grpName : self.zabbix_api.usergroup.getobjects(name=grpName)[0].get('usrgrpid')}

	def update_profile(self, usr, passwd, dict):
		
		""" Accepts Dictionary(items to update)and user's alias(reference). Returns boolean.
			Params: usr=alias, Dictionary=https://www.zabbix.com/documentation/2.4/manual/api/reference/user/object 
			Only given params will be updated.

			API Required Param: passwd, usrgrps
		"""
		
		if not User().is_user_exist(usr): return False
		print (self.zabbix_api.user.get(search={'alias':usr}, output='extend'))
		print (self.zabbix_api.user.update(passwd=passwd, usrgrps='14',alias='sam', name='SamKulit', userid=6))
		print (self.zabbix_api.user.get(search={'alias':usr}, output='extend'))
	
if __name__ == '__main__':

	auth_data = {
		'username': SUPERDUPER_ADMIN, 'password': SUPERDUPER_PASSWD, 
		'zabbix_url': ZABBIX_URL, '__connect': zabbix_connect
	}

	handler = type('handler', (object, ), auth_data) 
	zobj = handler().__connect()
	zabbix_api = ZabbixAdapter(zobj)
		
	'''
	result = zabbix_api.getAllUsers()['result']
	result = zabbix_api.screen_data()['result']
	result = zabbix_api.graph_data()['result']	
	result = zabbix_api.get_items()['result']
	result = zabbix_api.host_get()['result']
	result = zabbix_api.host_group()['result']
	result = zabbix_api.httptest()['result']
	result = zabbix_api.host_get()['result']

	for res in result:
		for key in res.iterkeys():
			print '%s : %s' %(key, res[key])

		##print('\tgetting item for : %s' %res['hostid'])
		##res = zabbix_api.item_get(res['hostid'])['result']
		##for i in res:
		##	for k in i.iterkeys():
		##		print '\t%s : %s' %(k, i[k])

		print "=================================================\n"
	
	#key_ = "system"
	#key_ = "fs"
	#key_ = "vm.memory.size[free]"
	#key_ = "vm.memory.size"
	#key_ = "vfs.fs.size"
	#key_ = "net.if.in|out"
	#key_ = "net.if"
	#key_  = "web.test.in"
	#hostid = 10124 # 10107
	#print('getting item for host_id : %d' %hostid)
	#result = zabbix_api.item_get(hostid, key_)['result']
	
	
	result = zabbix_api.host_get()['result']
	for res in result:
		for key in res.iterkeys():
			print '\t%s : %s' %(key, res[key]) ##value)
			
		#print('%s' %res['hostid'])
		#items = zabbix_api.item_get(res['hostid'])['result']
		#hostgroups = zabbix_api.discover_host(res['hostid'])['result']
		#print hostgroups
		#for item in items:
			
		#	print item

			#for key in item.iterkeys():
			#	print '\t%s : %s' %(key, item[key]) ##value)
			#break
		##if not int(res['lastns']):
		##	continue
		##print res['key_'], res['lastvalue']

		#for key in res.iterkeys():
		#	print 
			##if key in ['name','key_', 'lastvalue', 'lastclock', 'prevvalue', 'lastns', 'description' ]:
				##print(key, res[key])
			#if key in ['lastns', 'prevvalue', 'lastvalue', 'lastclock'] and res[key] in [u'0.0',u'0.00', u'0.0000']:
			#	continue
			#if key == 'lastvalue' or key == 'prevvalue':
			#	value = zabbix_api.format_size(res[key])
			#else:
			#	value = res[key]
			
			#print '\t%s : %s' %(key, res[key]) ##value)
		
		print "=================================================\n"
	#'''