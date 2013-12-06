import logging

from twisted.internet import defer, protocol, reactor
from thor.application import client

class Server(protocol.ServerFactory):
    
    def __init__(self, iface='0.0.0.0', port=21189):
        self.logger = logging.getLogger('thor.application.Server')
        
        self.iface = iface
        self.port = port
        
        self.socket = None
        self.started = False
        
        self.clients = []
        
    def __str__(self):
        return '[Server <%s:%s> status=%s]' % (self.iface, self.port, self.started)
        
    def _cbStartup(self, result):
        self.started = True
        
        self.logger.debug('Startup sequence completed')
        
        # Call the protocol factory's startService method and run any code there
        # first before we initialize the routines within our custom method here
        protocol.ServerFactory.startFactory(self)
        
        return result

    def _ebStartup(self, failure):
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")        
        
        # TODO handle the failure
            
    def buildProtocol(self, addr):
        
        c = client.Connection()    
        self.clients.append(c)
        
        return c
    
    def isActive(self):
        # TODO More lgical checks here
        return self.started
        
    
    def shutdown(self):
        self.logger.debug('Server shutdown started')
        d = self.stopServer()        
        return d
    
    def shutdownHook(self):
        self.logger.info('shutdownHook() called')
        d = defer.Deferred()
        # Perform additional shutdown tasks.
        # For now this is just a placeholder for future extension.       
        return d
                
    def startedConnecting(self, connector):
        #self.logger.debug('Incomming connection from <%s:%s> accepted', 
        #    addr.host, addr.port)
        print dir(connector)
    
    def startServer(self):
        d = self.startDeferred = defer.Deferred()        
        # Log a debug message that our server has begun warming up and is almost 
        # ready to accept new connections
        self.logger.debug('Starting server listening on <%s:%s>' % (self.iface, self.port))
        # The following methods allow for a startup hook to be called when the 
        # startup is successful or when an error has occured
        d.addCallback(self._cbStartup)
        d.addErrback(self._ebStartup)
        # Ignite the reactor and begin the service
        # The startupHook will be the entry point to the internal server(s) and
        # components of the service
        reactor.callWhenRunning(self.startupHook, d)
        
    def startupHook(self, startServiceDeferred):
        # Perform additional startup tasks.
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the startServiceDeferred.
        startServiceDeferred.callback(True)
    
    def stopServer(self):
        self.logger.debug('Stopping server listening on <%s:%s>' % (self.iface, self.port))
        # Here we want to return a default deferred object when we have run the
        # shutdown routines successfully. In stopping the server we want to stop
        # all connections and then wiat for them to be successfully closed
        self._serverShutdown = protocol.ServerFactory.stopFactory(self)
        
        if not self._serverShutdown:
            self._serverShutdown = defer.Deferred()
        
        if self.started:
            self._serverShutdown.chainDeferred(self.shutdownHook())
        self.started = False 
        
        if not self.clients:
            return self._serverShutdown
        
        clientShutdown = defer.Deferred()
        for client in self.clients:
            client.sendMessage('Test write before shutdown')  
            clientShutdown.chainDeferred(client.shutdown())
            
        self._serverShutdown.chainDeferred(clientShutdown)
               
        from thor.application.service import allConnectionsClosed
        self._serverShutdown.chainDeferred(allConnectionsClosed(self))
        
        return self._serverShutdown
        