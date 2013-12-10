import os
import json
import logging

from twisted.protocols import basic 
from twisted.internet import defer

class Connection(basic.LineReceiver):
    
    _connection_lost = None
    
    def __init__(self, factory):
        self.logger = logging.getLogger(__name__)
        self.factory = factory
        
        from thor.common.identity import generate_uid
        self.uid = generate_uid()
    
    def connectionMade(self):        
        self.sendLine("Connection established from process %s" % (os.getpid()))
        self._connection_lost = defer.Deferred()
        
    def connectionLost(self, reason):
        
        if reason:
            self.logger.info('[1] Disconnected %s' % (reason))
        else:
           self.logger.info('[1] Disconnected')
           
        self._connection_lost.callback(True)
        self.factory.notifyServerConnectionLost(self)
    
    def exit(self):
        self.transport.abortConnection()
        
    def notifyConnectionLost(self):
        if self._connection_lost is not None:
            return self._connection_lost
        return defer.succeed(None)
        
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