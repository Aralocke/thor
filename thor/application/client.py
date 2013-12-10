import os
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
        # The connection has been established so we setup teh deferred that gets
        # fired when we begin our disconnection routine called from connectionLost
        self._connection_lost = defer.Deferred()
        
    def connectionLost(self, reason):
        
        if reason:
            self.logger.info('[1] Disconnected %s' % (reason))
        else:
           self.logger.info('[1] Disconnected')
        
        # Fire our connection lost callback.
        self._connection_lost.callback(True)
        
        # Notify the server we belong to that we have officially lost our connection
        # and no longer viable. This will remove us from the known connections
        # list in the server
        self.factory.notifyServerConnectionLost(self)
        
    def notifyConnectionLost(self):
        # Returns the deferred that will be fire in the event of the client 
        # actually disconnecting from the socket. This is triggered by the 
        # connectionLost method and therefore is the only reliable way to
        # know if the conenction has been finished
        if self._connection_lost is not None:
            return self._connection_lost
        
        # We're not shutting down, so just return a deferred that says we did
        # whatever options we've been asked of and hope for this best
        return defer.succeed(None)
        
    def shutdownHook(self):
        # The shutdownHook is entirely application logic for the shutdown code
        # All of the code here will happen BEFORE the actual shutdown of the 
        # connection occurs by the reactor loop
        d = defer.Deferred()
        
        # Alert the connection that we are shutting down        
        self.sendMessage('Disconnecting')
        
        # Wrap up the application logic by callign loseCOnnection which will
        # wait for the writers to finish the buffers off and exit out of the 
        # client
        self.transport.loseConnection()
        
        # We MUST return a deferred becaus ethis gets chained to the networking 
        # logic the occurs when the shutdown method is called by the server
        return d
        
    def shutdown(self):
        # The shutdown function is called form the servers running them. This 
        # function will return a deferred that calls the application logic 
        # function in the shutdownHook
        d = defer.Deferred()
        
        # TODO Client shutdown logic
        
        # Chain the shutdownHook deferred to the call stack of the shutdown.
        # the application logic is separate from alerting teh server that the 
        # connection has actually been terminated in the asynchronous loop
        d.chainDeferred(self.shutdownHook())        
        return d
                
    def lineReceived(self, data):
        print 'Recieved ->', data
        
    def sendMessage(self, message):
        self.sendLine(message)