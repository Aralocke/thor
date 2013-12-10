import logging

from twisted.internet import defer, protocol, reactor
from thor.application import client

class Server(protocol.ServerFactory):
    
    _serverShutdown = None
    
    def __init__(self, asgard, iface='0.0.0.0', port=21189):
        self.logger = logging.getLogger('thor.application.Server')
        
        self.asgard = asgard
        
        self.iface = iface
        self.port = port
        
        self.socket = None
        self.started = False
        
        self.clients = {}
        
        from thor.common.identity import generate_uid
        self.uid = generate_uid()
        
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
        # In the case of catastrohpic failure during the startup of this server
        # the sequence will call this errback
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")        
        
        # TODO handle the failure
        
    def allConnectionsClosed(self):
        # Returns the deferred that we will fire during the shutdown sequence
        # This will ONLY fire during a shutdown sequence that has been called by 
        # the Asgard service
        if self._serverShutdown is not None:
            return self._serverShutdown
        
        # We're not shutting down, so just return a deferred that says we did
        # whatever options we've been asked of and hope for this best
        return defer.succeed(True)
            
    def buildProtocol(self, addr):   
        # Create a new client
        c = client.Connection(self)
        # We save all new clients by uid on the server. This allows us to track 
        # them and then shut them down based on their connection ID
        self.clients[c.uid] = c 
        
        return c
    
    def isActive(self):
        # TODO More lgical checks here
        return self.started 
    
    def notifyServerConnectionLost(self, client):
        # Here we get called by the client as it goes through its own shutdown 
        # process.  During the lostConnection code block this gets called to 
        # remove the connection from the parent server dictionary
        if client.uid in self.clients:     
            del self.clients[client.uid]            
        
        # Given we have shutdown our LAST connection and have begun shutting
        # down the application, we will fire off Asgard's notify to remove the 
        # server from its memory. Each server will block the shutdown process 
        # until it has shutdown its connections
        if not self.clients and self._serverShutdown:
            # We have no more connections so we chain the correspondign notify in 
            # Asgard to our shutdown here triggering our callback chain and 
            # finishing up teh shutdown of the server
            self._serverShutdown.addCallback(self.asgard.notifyServerShutdown)
            # Fire our callback chain which will remove ourselves from Asgard
            self._serverShutdown.callback(self)
    
    def shutdownHook(self):
        d = defer.Deferred()
        # Perform additional shutdown tasks.        
        # For now this is just a placeholder for future extension.       
        return d
                
    def startedConnecting(self, connector):
        #self.logger.debug('Incomming connection from <%s:%s> accepted', 
        #    addr.host, addr.port)
        pass
    
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
        
    def shutdown(self):
        self.logger.debug('Server shutdown started')
        
        # We are shutting down the server and starting a chain that will close
        # all of the open connections and shut down the listening socket we
        # are using here
        if self._serverShutdown is None:
            self._serverShutdown = defer.Deferred()
        
        # Use the reactor to asynchronously shut us down while we initiate the
        # shutdown of our connections. This method will only fire given the server
        # has already been started
        if self.started:
            reactor.callFromThread(self.stopServer)
        
        # This deferred chain will do nothing if the server has not already been
        # started
        return self._serverShutdown
    
    def stopServer(self):
        self.logger.debug('Stopping server listening on <%s:%s>' % (self.iface, self.port))
        # Here we want to return a default deferred object when we have run the
        # shutdown routines successfully. In stopping the server we want to stop
        # all connections and then wiat for them to be successfully closed
        status = protocol.ServerFactory.stopFactory(self)
        
        if not status:
            status = defer.Deferred()
        
        # When we don't have any clients we will remove ourselves from asgard quickly
        # and let the rest of teh shutdown happen on its own. WIthout teh server 
        # removing itself from asgard quickly we will continue to wait for a 
        # deferred chain that may never fire
        if not self.clients:
            self.asgard.notifyServerShutdown(self)
        else:
            # Loop through all available clients and initiate their shutdown
            # sequences. This allows us to send any remainign data and alert the
            # clients that we are shutting down
            for uid, client in self.clients.iteritems():
                client.sendMessage('Test write before shutdown') 
                # We allow the clients to shutdown asynchronously and in doing so
                # ensure that their remaining data will be sent before the transport
                # gets closed cleanly by the reactor
                reactor.callFromThread(client.shutdown)
        
        # Give us the ability to add some programmable exit logic to the application
        # without changing the exit routine. Any extended applictaion logic should go
        # in the shutdownHook() function becaus eit gives us teh separation between 
        # server logic and application logic
        if self.started:
            status.chainDeferred(self.shutdownHook())
        self.started = False       

        return status