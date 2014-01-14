from thor.application.events import event
from thor.common.identity import generate_uid

class Connection(object):

	_eventTriggers = {}
	_state = None
	factory = None

    def __init__(self):
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Connection')

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

    def removeEventTrigger(self, triggerID):
        pass

    def setState(self, state):
        self._state = state

	def shutdown(self):
		pass

    def shutdownHook(self, shutdown):
        # Perform additional shutdown tasks
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the shutdown deferred.
        shutdown.callback(None)
        # Returns None

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