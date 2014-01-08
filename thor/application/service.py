import logging
import os
import signal
import sys

from twisted.application import internet, service
from twisted.internet import defer, reactor
from thor.application.events import event
from thor.common import status, utils
from thor.common.identity import generate_uid

class BaseService(service.MultiService):

    _state = None
    
    def __init__(self, parent=None):
        # Initialize the Multi Service
        service.MultiService.__init__(self)
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Service')
        # The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
        self.uid = generate_uid()

        self.setState('NEW')

        self._eventTriggers = {}
        
    def addEventTrigger(self, phase, eventType, function, *args, **kwargs):
        assert callable(function), "%s is not callable" % function
        if eventType not in self._eventTriggers:
            self._eventTriggers[eventType] = event.ThreePhaseEvent()
        triggerID = self._eventTriggers[eventType].addTrigger(phase, function,
            *args, **kwargs)
        return (eventType, triggerID)

    def fireEventTrigger(self, eventType):
        print '-> received event :: %s -> %s' % (eventType, self.uid)
        event = self._eventTriggers.get(eventType)
        if event is not None:
            event.fireEvent() 

    def removeEventTrigger(self, triggerID):
        pass

    def setState(self, state):
        print 'Changing state to: %s -> %s' % (state, self.uid)
        self._state = state

    def _shutdownService(self, passThrough=None):
        print 'Service shutting down -> %s' % self.uid
        # Set the boolean for the service to shutdown this should prevent
        # extra calls to the shutdown events after they physically shutdown
        self.setState('STOPPED')

        # Return the result from the callback chain and get outta dodge
        return passThrough
    
    def _shutdownError(self, failure=None):
        # We're shutting down, so do we actually care what happens in here?
        pass

    def shutdown(self):
        print 'shutdown called -> %s' % self.uid        
        # Shutdown the service permenantly by setting this flag. There is a possible
        # chance that the reactor shutdown trigger might go off again so this
        # will prevent two calls to reactor.stop()
        if self._state == 'RUNNING': 
            # After this point we begin shutting down all of the services in our
            # application gracefully and waiting on sockets to shut down properly
            self.__shutdown = defer.Deferred()
            # CHange state to stopping and alert the rest of the application
            self.setState('STOPPING')
            # Disown the parent services and trigger the stopService command to run
            print 'Disowning parent service'
            service.MultiService.disownServiceParent(self)
            # Add an internal hook for the shutdown methods. This allows us to handle
            # any potential errors during shutdown as well as run our own code
            # during shutdown. 
            self.__shutdown.addCallbacks(self._shutdownService, self._shutdownError)     
            # The reactor should also call the shutdown hook allowing us to chain 
            # any functional code to the shutdown process. The hook method is for
            # extending classes primarily
            reactor.callWhenRunning(self.shutdownHook, self.__shutdown)
            # Fire a system event for a shutdown
            self.fireEventTrigger('shutdown')
            # Stop service returns a deferred or a None value in this case
            # we actually wait until the shutdown has completed to initialize a 
            # graceful shutdown of the application
            return self.__shutdown

        return None

    def shutdownHook(self, shutdown):
        # Perform additional shutdown tasks
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the shutdown deferred.
        shutdown.callback(None)
        # Returns None

    def _startupService(self, passThrough=None):
        # This callback really starts the service by setting the service status
        # variable and igniting the service parent classes
        self.setState('RUNNING')
        # Return the result from the callback chain and get outta dodge
        return passThrough

    def _startupError(self, passThrough=None):
        # This errback shuts us down if an error occured in process pool startup
        #
        # Log messages here to know about the failure and then shut down the 
        # reactor before anythign else can start up
        #
        # TODO Handle failures and provide better catastrophe logs
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")
        # Some kind of world ending error just happened here. If the logs appear 
        # useful, please tell somebody who knows what they are doign with this
        # application

    def startup(self):
        self.setState('STARTING')
        # Create the deferred that will be lit by the reactor igniting the service
        d = defer.Deferred()
        # The following methods allow for a startup hook to be called when the 
        # startup is successful or when an error has occured
        d.addCallbacks(self._startupService, self._startupError)
        # Fire the system event for a startup event
        self.fireEventTrigger('startup')
        # Ignite the reactor and begin the service
        # The startupHook will be the entry point to the internal server(s) and
        # components of the service
        reactor.callWhenRunning(self.startupHook, d) 

    def startupHook(self, startup):
        # Perform additional startup tasks.
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the startup deferred.
        startup.callback(None)
        # Returns None

    def startService(self):
        print 'startService -> %s' % self.uid
        service.MultiService.startService(self)

    def stopService(self):
        print 'stopService -> %s' % self.uid
        return service.MultiService.stopService(self)

class DaemonService(BaseService):

    def __init__(self, daemon=True):
        # Initialize the Multi Service
        BaseService.__init__(self)   

    def _shutdownService(self, passThrough=None):

        if self._state == 'STOPPING':
            self.logger.info('Reactor shutdown ... NOW') 
            reactor.stop()

        return BaseService._shutdownService(self)   

    def _startupError(self, failure=None):
        # We call the older method because it will handle logging of the error
        BaseService.serviceStartupError(self, failurre=failure)
        # Since this is a daemon process, failure to startup needs to result in the
        # shutdown of the application and the reactor
        #
        # The mains service failed to start, we're now down and getting
        # out of here
        reactor.stop()
