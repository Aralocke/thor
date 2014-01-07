import logging
import os
import signal
import sys

from twisted.application import internet, service
from twisted.internet import defer, reactor
from thor.application.events import trigger
from thor.common import status, utils
from thor.common.identity import generate_uid

class BaseService(service.MultiService, trigger.Triggers):
    
    _systemFlags = None
    
    def __init__(self):
        # Initialize the Multi Service
        service.MultiService.__init__(self)
        # Initialize the triggers and event system
        trigger.Triggers.__init__(self)
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Service')
        # Boolean flag to decided whether or not we have started properly. This
        # flag will be set true when the startup service has been called and 
        # hooked properly
        self.started = False
        # The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
        self.uid = generate_uid()
        
    def initialize(self):
        pass

    def setApplication(self, application):
        # Set the ervice parent, this is the actual twisted application. The only 
        # implementation that overrides this are the primary services: Asgard and
        # Crawler. Which each maintain a reference to the application for starting 
        # other services
        service.MultiService.setServiceParent(self, application)

    def serviceShutdown(self, passThrough=None):
        print 'Service shutting down -> %s' % self.uid
        # Set the boolean for the service to shutdown this should prevent
        # extra calls to the shutdown events after they physically shutdown
        self.started = False
        # Return the result from the callback chain and get outta dodge
        return passThrough
    
    def serviceShutdownError(self, failure=None):
        # We're shutting down, so do we actually care what happens in here?
        pass
        
    def serviceStartup(self, passThrough=None):
        # This callback really starts the service by setting the service status
        # variable and igniting the service parent classes
        self.started = True
        # Return the result from the callback chain and get outta dodge
        return passThrough
    
    def serviceStartupError(self, failure=None):
        # This errback shuts us down if an error occured in process pool startup
        #
        # Log messages here to know about the failure and then shut down the 
        # reactor before anythign else can start up
        #
        # TODO Handle failures and provide better catastrophe logs
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")
        
        # The mains service failed to start, we're now down and getting
        # out of here
        reactor.stop()
        
        # Some kind of world ending error just happened here. If the logs appear 
        # useful, please tell somebody who knows what they are doign with this
        # application
        
    def shutdownHook(self, shutdown):
        # Perform additional shutdown tasks
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the shutdown deferred.
        shutdown.callback(None)
        # Returns None
        
    def startupHook(self, startup):
        # Perform additional startup tasks.
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the startup deferred.
        startup.callback(None)
        # Returns None
        
    def startService(self):     
        # Fire the initialization event here
        self.fireEventTrigger('initialize')   
        # Call the parent function first to setup the co-routines used by the 
        # rest of the service BEFORE we implement our own servers
        service.MultiService.startService(self)
        # Create the deferred that will be lit by the reactor igniting the service
        d = defer.Deferred()
        # The following methods allow for a startup hook to be called when the 
        # startup is successful or when an error has occured
        d.addCallbacks(self.serviceStartup, self.serviceStartupError)
        # Fire the system event for a startup event
        self.fireEventTrigger('startup')
        # Ignite the reactor and begin the service
        # The startupHook will be the entry point to the internal server(s) and
        # components of the service
        reactor.callWhenRunning(self.startupHook, d) 
        
    def stopService(self):
        # After this point we begin shutting down all of the services in our
        # application gracefully and waiting on sockets to shut down properly
        d = service.MultiService.stopService(self)
        # Logical check to ensure we ALWAYS return a deferred on this function 
        # call
        if d is None: d = defer.Deferred()
        # Shutdown the service permenantly by setting this flag. There is a possible
        # chance that the reactor shutdown trigger might go off again so this
        # will prevent two calls to reactor.stop()
        if self.started: 
            status = defer.Deferred()
            # Add an internal hook for the shutdown methods. This allows us to handle
            # any potential errors during shutdown as well as run our own code
            # during shutdown. 
            status.addCallbacks(self.serviceShutdown, self.serviceShutdownError)
            # The reactor should also call the shutdown hook allowing us to chain 
            # any functional code to the shutdown process. The hook method is for
            # extending classes primarily
            reactor.callWhenRunning(self.shutdownHook, status)
            # Fire a system event for a shutdown
            self.fireEventTrigger('shutdown')
        # Stop service returns a deferred or a None value in this case
        # we actually wait until the shutdown has completed to initialize a 
        # graceful shutdown of the application
        return d 

class DaemonService(BaseService):

    def __init__(self, daemon=False):
        # Initialize the Multi Service
        BaseService.__init__(self)
        # If we ARE a daemon service we will shutdown the reactor when we have
        # completed our shutdown
        self.daemon = daemon

    def setApplication(self, application):
        # We maintain a reference to the application parent application that we 
        # belong to
        self.application = application
        # After we save the reference call the base class method and begin 
        # running things here
        BaseService.setApplication(self, application)

    def setDaemonService(self, status=False):
        self.daemon = status

    def serviceShutdown(self, passThrough=None):
        # We will add an extra callback to shutdown the reactor if we are a daemon service
        # in any application there should only be one daemon application
        if self.daemon and self.started:
            self.logger.info('Reactor shutdown ... NOW')
            reactor.stop()
        # Call the existing serviceShutdown method to preserve functionality
        # that we don't want to include here
        BaseService.serviceShutdown(self, passThrough)
        # Return the result from the callback chain and get outta dodge
        return passThrough