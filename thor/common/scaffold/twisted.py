from twisted.application import internet, service
from twisted.internet import defer, reactor
from thor.common.scaffold import foundation

class TwistedSystem(foundation.StatefulSystem):
	# No pun intended

	def shutdown(self, passThrough=None):
        # Shutdown the service permenantly by setting this flag. There is a possible
        # chance that the reactor shutdown trigger might go off again so this
        # will prevent two calls to reactor.stop()
		if self.getState() == 'RUNNING': 
			# After this point we begin shutting down all of the services in our
			# application gracefully and waiting on sockets to shut down properly
			self.__shutdown = passThrough or defer.Deferred()
			# CHange state to stopping and alert the rest of the application
			self.setState('STOPPING')
			# Disown the parent services and trigger the stopService command to run
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
	pass

class Service(TwistedSystem, service.Service):
	def __init__(self):
		# Initialize the Twisted Service here
		service.Service.__init__(self)

class MultiService(TwistedSystem, service.MultiService):
	def __init__(self):
		# Initialize the Twisted Service here
		service.MultiService.__init__(self)