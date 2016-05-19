#! /usr/bin/env python

# ----------------------------------------------------------
## script runs every 5mins
# 1. verify database access
# 2. checik if there is an active anomaly report
    # - halt the process    
# 3. check api connection
    # if unable to connect send email and save anomaly to db
# 4. check if kpi values has zero data
    # if exist send email and save anomaly to db
# ----------------------------------------------------------
        
import sys
import os
import string
import pycurl
import StringIO
import time
import urllib2
import requests
from urlparse import urlparse, urljoin
from xml.dom.minidom import parseString
from datetime import datetime, date
import ConfigParser
from traceback import print_exc
from clint.textui import colored

from EmailConstructorClass import SMTPConn, _HTMLWithAttachments
from ModelClass import *


def read_api_settings():

    try: sys.frozen
    except AttributeError:
        try: me = __file__
        except NameError: me = sys.argv[0]
    else: me = sys.executable

    ini = os.path.splitext(os.path.abspath(me))[0]+'.ini'
    settings = ConfigParser.RawConfigParser()
    settings.readfp(open(ini, 'r'), ini)
    return settings

def add_recipients(msg, recipients, type):

    emails = map(lambda email: email, recipients.split(';'))
    for email in emails:
        msg.add_recipient(email, None, type)

class KPIAlertException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(
            colored.red(self.value)
        )

class KPIAnomalyChecker(object):

    def __init__(self):
        
        self.__settings = read_api_settings()

        self.__server   = self.__settings.get('MAILINFO', 'SERVER')
        self.__port     = self.__settings.get('MAILINFO', 'PORT')
        self.__user     = self.__settings.get('MAILINFO', 'USER')
        self.__passwd   = self.__settings.get('MAILINFO', 'PASSWD')
        self.__subject  = self.__settings.get('MAILINFO', 'SUBJECT')
        self.__resolved = self.__settings.get('MAILINFO', 'RESOLVED')
        self.__anomaly  = self.__settings.get('MAILINFO', 'ANOMALY')
        self.__sender   = self.__settings.get('MAILINFO', 'SENDER')
        self.__mfrom    = self.__settings.get('MAILINFO', 'FROM')
        self.__to       = self.__settings.get('MAILINFO', 'TO')
        self.__cc       = self.__settings.get('MAILINFO', 'CC')
        self.__bcc      = self.__settings.get('MAILINFO', 'BCC')

        self.__host     = self.__settings.get('MYSQL', 'HOST')
        self.__dbname   = self.__settings.get('MYSQL', 'DBNAME')
        self.__username = self.__settings.get('MYSQL', 'USERNAME')
        self.__password = self.__settings.get('MYSQL', 'PASSWORD')

        self.__class_model = ModelClass(
                dbname=self.__dbname, user=self.__username, 
                password=self.__password, host=self.__host
            )

    def get_date_time(affixTime=0):
        
        if affixTime: 
            return datetime.strftime(
                datetime.now(), "%Y-%m-%d %H:%M:%S"
            )
        else:
            return date.today()

    def get_base_url(self, site):

        urlparts = urlparse(site)
        return '%s://%s' %(
            urlparts.scheme, urlparts.netloc
        )

    def inspect_anomaly(self, todayis):
        
        isActive = 0
        if not self.__class_model.db_connect():
            raise KPIAlertException(
               "Unable to connect to host database"
            )

        print colored.yellow(
            'Checking record if there is an active anomaly.'
        )
        resultset = self.__class_model.select_query(
            "SELECT id FROM alerts WHERE is_active = 1"
        ) 
        
        if resultset:
            print colored.red(
               "There is an active anomaly report, please verify!."
                )
            return 1

        return isActive

    def save_anomaly(self, site, todayis, anomaly): 

        isNotSave = 0
        if not self.__class_model.db_connect():
            raise KPIAlertException(
               "Unable to connect to host database"
            )
            return 1
            
        print colored.yellow(
            'Saving Anomaly Record'
        )
        statement = """
                INSERT INTO alerts 
                (sitename, dateandtime, description, is_active) 
                VALUES('%s', '%s', '%s', 1) 
                """ %(site, todayis, anomaly)
        resultset = self.__class_model.insert_query(statement) 
        
        if resultset:
            raise KPIAlertException(
               "There is an active anomaly report, please verify!."
            )
            return 1

        return isNotSave

    def clear_anomaly(self):

        isNotSave = 0
        if not self.__class_model.db_connect():
            raise KPIAlertException(
               "Unable to connect to host database"
            )
            return 1
            
        print colored.yellow(
            'Clearing Anomaly Record...'
        )
        resultset = self.__class_model.update_query(
            "UPDATE alerts SET is_active=0"
            ) 
        if resultset:
            raise KPIAlertException(
               "There is an active anomaly report, please verify!."
            )
            return 1

        return isNotSave

    def verify_api_access(self, api):

        response = requests.get(api)
        return response.status_code, response.reason

    def read_api_response(self, site):

        resultDict = {}
        anomaly_found = ''
        
        response = urllib2.urlopen(site)
        dom      = parseString(response.read())
        root     = dom.documentElement
        rows     = dom.getElementsByTagName('row')
        
        for row in rows:
            columns = row.getElementsByTagName('column')
            for column in columns:
                name  = column.getAttribute("name").encode('ascii','ignore')
                value = column.firstChild.nodeValue.encode('ascii','ignore')
                resultDict.update({name:value})
        
        for key, value in resultDict.items():
            if value in ('0', 0):
                anomaly_found = '<br/>'.join(
                    "%s = %s" %(key,val) for (key, val) in content.iteritems()
                    )
                anomaly_found = "SITE: %s<p/>%s" %(site, anomaly_found)

        return anomaly_found

    def send_anomaly_report(self, anomaly, resolved=0):

        msg               = _HTMLWithAttachments()
        msg.sender_name   = self.__sender
        msg.sender_email  = self.__mfrom
        msg.subject       = self.__subject
        if resolved: html = file(self.__resolved).read() %locals()
        else: html        = file(self.__anomaly).read() %locals()
        msg.html          = html
        add_recipients(msg, self.__to, 'To')
        add_recipients(msg, self.__bcc, 'Bcc')
        try:
            mail = SMTPConn(self.__server, self.__port)
            mail.connect()
            mail.ehlo()
            if mail.has_extn('STARTTLS'): 
                mail.starttls()
                mail.ehlo()
            mail.login(self.__user, self.__passwd)
            mail.send_message(msg)
        except: 
            raise KPIAlertException(
               "An error occured when trying to send anomaly report."
            )
        finally: mail.quit()
   
    def check_kpi_anomalies(self):

        todayis = self.get_date_time()
        print colored.yellow('Start Process: %s'%todayis)

        active_anomaly = self.inspect_anomaly(todayis)
        anomaly_found = ''

        for site, url in SERVERS.items():

            apiurl = url %locals()
            base_url = self.get_base_url(apiurl)

            print colored.blue("Connecting to %s site API..." %site)
            code, status = self.verify_api_access(base_url) 
            if  code != 200 and status != 'OK':
                print colored.red(
                    "%s >>> API is unreachable.\nSending Anomaly Report." %base_url
                )
                anomaly_found = 'SITE: %s<br/>ERROR: API is Unreachable(%s)' %(
                        site, base_url
                    )
                if not active_anomaly:
                    self.send_anomaly_report(anomaly_found)
                    self.save_anomaly(site, todayis, anomaly_found)
                break

            print colored.green(
                'Able to access %s. Trying to get content.\n%s' %(
                    site, apiurl)
                )
            #anomaly_found = 'SITE: %s<br/>Logins = 02<br/>Deposits = 12345<br/>Games = 0' %site
            anomaly_found = self.read_api_response(apiurl)
            if anomaly_found:
                if not active_anomaly:
                    print colored.red(
                        'Found anomaly in KPI Report on %s server.\nSending alerts now.'%(site)
                        )
                    self.send_anomaly_report(anomaly_found)
                    self.save_anomaly(site, todayis, anomaly_found)
                else:
                    print colored.red(
                        'Found anomaly on %s server and there is an existing anomaly for verification.' %site
                        )
                break
            else:
                print colored.red('Found no anomaly on %s server....' %site)
        
        if not anomaly_found:
            if active_anomaly:
                print colored.blue(
                    'Found no anomalies on all servers, clearing previous anomaly reported.'
                    )
                self.send_anomaly_report(anomaly_found, 1)
                self.clear_anomaly()

        print colored.yellow(
            'End Process: %s\n---------------------------'%(
                self.get_date_time()
                )
            )

def main():
    
    kpi = KPIAnomalyChecker()
    kpi.check_kpi_anomalies()

if __name__ == "__main__":

    main()