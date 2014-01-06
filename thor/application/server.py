import logging
import os
import signal
import sys

from twisted.internet import defer, protocol, reactor
from thor.application import service
from thor.common import status, utils

class Server(service.BaseService):
    
    def __init__(self, asgard=None):
        # initialize the base service and the parent classes
        service.BaseService.__init__(self)

        self.logger = logging.getLogger('thor.application.Server')
        # Boolean flag to decided whether or not we have started properly. This
        # flag will be set true when the startup service has been called and 
        # hooked properly
        self.started = False
        
        self.asgard = asgard

    def initialize(self):
        print 'initialize -> %s' % self.uid

    def setServiceParent(self, parent):
        # We're overriding this so that we have our own record of the asgard
        # service that we belong too
        self.asgard = parent
        # Then we pass it along the chain to the twisted service
        service.BaseService.setServiceParent(self, parent)

    def startService(self):
        print 'startService -> %s' % self.uid
        service.BaseService.startService(self)

    def startupHook(self, startup):
        print 'Server startupHook called'
        startup.callback(None)

    def stopService(self):
        print 'stopService -> %s' % self.uid
        return service.BaseService.stopService(self)