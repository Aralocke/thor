from zope.interface import implements, Interface, Attribute

from thor.common import identity
from thor.common.scaffold import hook, trigger
from thor.application.events import event

class IIdentifiable(Interface):
	def getUID():
		"""
        Returns the UID string for this class. The UID is created by the generate_uid
        function to meet a uniform standard. 

        It is a random string that is used solely for identification of runtime objects
		"""

class IStatefulService(Interface):

	def getState():
		"""
        Returns the state of the application.
		"""

	def setState(state):
		"""
        Set the state of the application. This allows us to track what phase
        or operating mode we are currently in. Eg: STARTING, RUNNING, STOPPING, 
        or STOPPED
		"""

class System(object):

	implements(hook.IHookService, IStatefulService)

	__state = None

	def getState(self):
		# SImple getter to retrieve the state value
		return self.__state

	def setState(self, state):
		# There shoudl probably be some kind of type checking here. For now all
		# we're doing is saving the state of the service and returning. 
		self.__state = state

	def shutdownHook(self, callback):
		# Perform additional shutdown tasks
		# This is a placeholder for future extension.
		# This function *MUST* callback / errback
		# the shutdown deferred.
		callback.callback(None)
		# Returns None

	def startupHook(self, callback):
		# Perform additional startup tasks.
		# This is a placeholder for future extension.
		# This function *MUST* callback / errback
		# the startup deferred.
		callback.callback(None)
		# Returns None

class StagedEventSystem(System):

	implements(trigger.IStagedTriggerable)

	def addEventTrigger(self, phase, eventType, function, *args, **kwargs):
		raise NotImplementedError('addEventTrigger needs to be implemented')

	def fireEventTrigger(self, eventType):
		raise NotImplementedError('fireEventTrigger needs to be implemented')

	def removeEventTrigger(self, triggerID):
		raise NotImplementedError('removeEventTrigger needs to be implemented')

class StatefulSystem(StagedEventSystem):

	implements(IIdentifiable)

	__uid = None

	def __init__(self):
		# The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
		self.__uid = identity.generate_uid()
		# We need to set an initial state for the System. All incarnations of this
		# class will start at the same state, and end at the same state. No user defined
		# state will exist in the beginning or end
		self.setState('NEW')

	def getUID(self):
		return self.__uid

	def shutdown(self, passThrough=None):
		raise NotImplementedError('shutdown needs to be implemented')

	def _shutdownService(self, passThrough=None):
		# Fire a system event for a shutdown
		self.fireEventTrigger('shutdown')
		# Set the boolean for the service to shutdown this should prevent
		# extra calls to the shutdown events after they physically shutdown
		self.setState('STOPPED')
		# Return the result from the callback chain and get outta dodge
		return passThrough
    
	def _shutdownError(self, failure=None):
		# We're shutting down, so do we actually care what happens in here?
		pass

	def startup(self, passThrough=None):
		raise NotImplementedError('startup needs to be implemented')

	def _startupService(self, passThrough=None):
		# This callback really starts the service by setting the service status
		# variable and igniting the service parent classes
		self.setState('RUNNING')
		# Return the result from the callback chain and get outta dodge
		return passThrough

	def _startupError(self, failure=None):
		# Some kind of world ending error just happened here. If the logs appear 
		# useful, please tell somebody who knows what they are doign with this
		# application
		pass