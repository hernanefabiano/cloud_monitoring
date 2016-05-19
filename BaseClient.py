import urllib2
import urllib
import json
import hmac
import base64
import hashlib
import re
import logging


logger = logging.getLogger(__name__)


class BaseClient(object):
    def __init__(self, api, apikey, secret):
        self.api = api
        self.apikey = apikey
        self.secret = secret

    def request(self, command, args):
        args['apikey']   = self.apikey
        args['command']  = command
        args['response'] = 'json'
        
        params=[]
        
        keys = sorted(args.keys())

        for k in keys:
            params.append(k + '=' + urllib.quote(args[k])) 
       
        query = '&'.join(params)

        signature = base64.b64encode(hmac.new(
            self.secret, 
            msg=query.lower(), 
            digestmod=hashlib.sha1
        ).digest())

        query += '&signature=' + urllib.quote_plus(signature)

        #logger.debug('** CS_API: URL = %s' % self.api)
        #logger.debug('** CS_API: QUERY = %s' % query)
        #logger.debug('** CS QUERY: %s?%s' % (self.api,query))

        response = urllib2.urlopen(self.api + '?' + query)
        decoded = json.loads(response.read())

        #logger.debug('** CS_API: RESPONSE:')
        #logger.debug(decoded)
       
        propertyResponse = command.lower() + 'response'
        if not propertyResponse in decoded:
            if 'errorresponse' in decoded:
                raise RuntimeError("ERROR: " + decoded['errorresponse']['errortext'])
            else:
                raise RuntimeError("ERROR: Unable to parse the response")

        response = decoded[propertyResponse]
        result = re.compile(r"^list(\w+)s").match(command.lower())

        if not result is None:
            type = result.group(1)

            if type in response:
                return response[type]
            else:
                # sometimes, the 's' is kept, as in :
                # { "listasyncjobsresponse" : { "asyncjobs" : [ ... ] } }
                type += 's'
                if type in response:
                    return response[type]

        return response
