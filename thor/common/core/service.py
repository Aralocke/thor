from twisted.application import service
from twisted.internet import defer
from twisted.python import log

from thor.common.core import component

RUN_OPT_ASGARD = 1
RUN_OPT_CRAWLER = 2
RUN_OPT_WEB = 3

class Service(component.Service, service.Service):
	
	def __init__(self, **kwargs):
		component.Service.__init__(self, **kwargs)

	def startService(self):
		# Set the state to an initialization state
		self.setState('INITIALIZE')
		# Fire the initialization hook - which happens before the service component
		# has been set to a running status
		self.fire('initialize')
		# Set the state to a starting state
		self.setState('STARTING')
		# Initialize the Twisted Service routines first. This will set the service
		# to running status and also execute any active services we have already added.
		#
		# By default this is book keeping only because there shouldn't be any services
		# added at this point (if this becomes a multiservice)
		service.Service.startService(self)
		# After we have setup the initialization routines of the service we call out own
		# startup hook. The goal is to split the twisted logic from application logic. 
		# Any startup implementation should be hooked to a stateful event. The follwoing
		# fires the startup event which should be the hook point for an implementing class
		self.fire('startup')
		# The state will persist at a starting state to allow any startup routines
		# to complete before changing to a RUNNING state
		self.setState('RUNNING')

	def stopService(self):
		# We only process the stopService once given that we are in a running state
		# as soon as this method gets called once, we shift our state to STOPPING
		# and this function can no longer be called successfully
		if self.getState('RUNNING'):
			# Set the state to a stopping state
			self.setState('STOPPING')
			# Call the MultiService stop service here which produces the deferred
			# that we will return. As long as this function is called at a valid time
			# we ALWAYS return a deferred
			d = service.Service.stopService(self) or defer.succeed(True)
			# Add callbacks to the shutdown functions. These catch errors and finish the 
			# shutdown process for us
			# Return the deferred and keep processing
			return defer.DeferredList([d, self.fire('shutdown')]).addCallbacks(
				self._shutdownService, self._shutdownError)
		# The stopService function will only return a deferred when the service is still
		# running and afterwards returns a None object
		return None

class MultiService(component.Service, service.MultiService):
	def __init__(self, **kwargs):
		service.MultiService.__init__(self)	
		component.Service.__init__(self, **kwargs)

	def startService(self):
		# Set the state to an initialization state
		self.setState('INITIALIZE')
		# Fire the initialization hook - which happens before the service component
		# has been set to a running status
		self.fire('initialize')
		# Set the state to a starting state
		self.setState('STARTING')
		# Initialize the Twisted Service routines first. This will set the service
		# to running status and also execute any active services we have already added.
		#
		# By default this is book keeping only because there shouldn't be any services
		# added at this point (if this becomes a multiservice)
		service.MultiService.startService(self)
		# After we have setup the initialization routines of the service we call out own
		# startup hook. The goal is to split the twisted logic from application logic. 
		# Any startup implementation should be hooked to a stateful event. The follwoing
		# fires the startup event which should be the hook point for an implementing class
		self.fire('startup')
		# The state will persist at a starting state to allow any startup routines
		# to complete before changing to a RUNNING state
		self.setState('RUNNING')

	def stopService(self):
		# We only process the stopService once given that we are in a running state
		# as soon as this method gets called once, we shift our state to STOPPING
		# and this function can no longer be called successfully
		if self.getState('RUNNING'):
			# Set the state to a stopping state
			self.setState('STOPPING')
			# Call the MultiService stop service here which produces the deferred
			# that we will return. As long as this function is called at a valid time
			# we ALWAYS return a deferred
			d = service.MultiService.stopService(self) or defer.succeed(True)
			# Add callbacks to the shutdown functions. These catch errors and finish the 
			# shutdown process for us
			# Return the deferred and keep processing
			return defer.DeferredList([d, self.fire('shutdown')]).addCallbacks(
				self._shutdownService, self._shutdownError)
		# The stopService function will only return a deferred when the service is still
		# running and afterwards returns a None object
		return None

class DaemonService(MultiService):
	def __init__(self, **kwargs):
		MultiService.__init__(self, **kwargs)