from thor.common.core import hook, object

class Component(object.Object, hook.Hooked):

	def __init__(self, **kwargs):
		object.Object.__init__(self)
		hook.Hooked.__init__(self)

		self.addHook('initialize', self.initialize)
		self.addHook('startup', self.startup)
		self.addHook('shutdown', self.shutdown)

		self.setState('NEW')

	def initialize(self, *args, **kwargs):
		pass

	def getState(self, state=None):
		if state is not None:
			if self.__state == state:
				return True
			else:
				return False
		return self.__state

	def setState(self, state):
		# Save the state of the component
		self.__state = state
		# Fire off the hook to any listeners that we have changed our state
		self.fire('state')

	def shutdown(self, *args, **kwargs):
		pass

	def startup(self, *args, **kwargs):
		pass

class BufferedComponent(Component):

    delimeter = '\r\n'
    bufflen = 16384
    __buffer = ''

    def clearLineBuffer(self):
	    # Clear the buffered data
	    _buffer, self.__buffer = self.__buffer, ''                
	    # return the data that was in the buffer for clean up purposes
	    return _buffer

class Connection(Component):

	def __init__(self):
		# Call the parent init function
		Component.__init__(self)	

class Service(Component):

	def __init__(self, **kwargs):
		# Call the parent init function
		Component.__init__(self, **kwargs)

	def _shutdownService(self, passThrough=None):
		# Set the boolean for the service to shutdown this should prevent
		# extra calls to the shutdown events after they physically shutdown
		self.setState('STOPPED')
		# Return the result from the callback chain and get outta dodge
		return passThrough
    
	def _shutdownError(self, failure=None):
		# We're shutting down, so do we actually care what happens in here?
		pass

	def _startupService(self, passThrough=None):
		# Fire a system event for a startup
		self.fire('startup')
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