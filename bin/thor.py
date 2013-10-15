import os
import sys

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__),
                                   os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from thor import request, response, service
from thor.common import utils

if __name__ == '__main__':
    
    scheme = 'http'
    target = 'phantomnet.net'
    uri = '/'
    
    r = request.Request(scheme=scheme, target=target, uri=uri)  
    print r
    
    curl_response = r.get()
    print curl_response
    
    serv = service.TestService()