import logging
import os
import signal
import sys

from twisted.application import service
from twisted.internet import defer, reactor
from thor.application.events import event
from thor.common import status, utils
from thor.common.scaffold import foundation

class TwistedSystem(foundation.StatefulSystem):
    # No pun intended

    _eventTriggers = {}
    __shutdownHook = None

    def __init__(self):
        foundation.StatefulSystem.__init__(self)

    def addEventTrigger(self, phase, eventType, function, *args, **kwargs):
        assert callable(function), "%s is not callable" % function
        if eventType not in self._eventTriggers:
            self._eventTriggers[eventType] = event.ThreePhaseEvent()
        triggerID = self._eventTriggers[eventType].addTrigger(phase, function,
            *args, **kwargs)
        return (eventType, triggerID)

    def fireEventTrigger(self, eventType):
        print '-> received event :: %s -> %s' % (eventType, self.getUID())
        event = self._eventTriggers.get(eventType)
        if event is not None:
            event.fireEvent() 

    def _startupError(self, passThrough=None):
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")

    def shutdown(self, passThrough=None):
        if self.__shutdownHook is None:
            if passThrough is not None: 
                self.__shutdownHook = passThrough
            else:
                self.__shutdownHook = defer.Deferred()
        # Shutdown the service permenantly by setting this flag. There is a possible
        # chance that the reactor shutdown trigger might go off again so this
        # will prevent two calls to reactor.stop()
        if self.getState() == 'RUNNING': 
            # CHange state to stopping and alert the rest of the application
            self.setState('STOPPING')            
            # Add an internal hook for the shutdown methods. This allows us to handle
            # any potential errors during shutdown as well as run our own code
            # during shutdown. 
            self.__shutdownHook.addCallbacks(self._shutdownService, self._shutdownError)     
            # The reactor should also call the shutdown hook allowing us to chain 
            # any functional code to the shutdown process. The hook method is for
            # extending classes primarily
            reactor.callLater(0, self.shutdownHook, self.__shutdownHook)            
        # Stop service returns a deferred or a None value in this case
        # we actually wait until the shutdown has completed to initialize a 
        # graceful shutdown of the application
        return self.__shutdownHook

    def startup(self, passThrough=None):
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

class Connection(TwistedSystem):
    def __init__(self):
        # Initialize our scaffold system
        TwistedSystem.__init__(self)

    def setParentService(self, parent):
        pass

class Service(TwistedSystem, service.Service):
    def __init__(self):
        # Initialize our scaffold system
        TwistedSystem.__init__(self)


    def _shutdownService(self, passThrough=None):
        # Disown the parent services and trigger the stopService command to run
        service.Service.disownServiceParent(self)

        # continue the chain
        return TwistedSystem._shutdownService(self, passThrough)

class MultiService(TwistedSystem, service.MultiService):
    def __init__(self):
        # Initialize the Twisted Service here
        service.MultiService.__init__(self)
        # Initialize our scaffold system
        TwistedSystem.__init__(self)

    def _shutdownService(self, passThrough=None):
        # Disown the parent services and trigger the stopService command to run
        service.MultiService.disownServiceParent(self)

        # continue the chain
        return TwistedSystem._shutdownService(self, passThrough)

class DaemonService(MultiService):

    def __init__(self, daemon=True):
        # Initialize the Multi Service
        MultiService.__init__(self)   

    def rehash(self):
        pass

    def _shutdownService(self, passThrough=None):

        if self.getState() == 'STOPPING':
            self.logger.info('Reactor shutdown ... NOW') 
            reactor.stop()

        return MultiService._shutdownService(self, passThrough)   