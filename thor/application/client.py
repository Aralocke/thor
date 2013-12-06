import os
import json
import logging

from twisted.protocols import basic 
from twisted.internet import defer

class Connection(basic.LineReceiver):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def connectionMade(self):        
        self.sendLine("Connection established from process %s" % (os.getpid()))
        
    def connectionLost(self, reason):
        
        if reason:
            self.logger.info('[1] Disconnected %s' % (reason))
        else:
           self.logger.info('[1] Disconnected')
           
    def disconnect(self, reason = None):
        self.transport.loseConnection()
        
    def shutdownHook(self):
        d = defer.Deferred()
        self.transport.loseConnection()
        return d
        
    def shutdown(self):
        d = defer.Deferred()
        self.sendMessage('Disconnecting')
        d.chainDeferred(self.shutdownHook())
        return d
                
    def lineReceived(self, data):
        print 'Recieved ->', data
        
    def sendMessage(self, message):
        self.sendLine(message)