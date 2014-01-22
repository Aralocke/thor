from twisted.internet import reactor
from thor.common.core import service
from thor.common.core.factories import unix

class UNIXConnection(service.ConnectionService):

	def __init__(self, path=None, protocol=None):
		# Call the parent init mechanism
		service.ConnectionService.__init__(self)
		# save the path to the socket we will be creating
		self.path = path
		# The factory we will be using is a UNIXClientFactory
		assert protocol, 'Protocol passed to UNIXConnection was nothing'
		self.factory = unix.UNIXClientFactory(self, protocol)	
		# The settings below come form handling the connection object 
		# that we are starting when we initiate a connection to Asgard
		self.connection = None
		# Default timeout before giving on on a socket
		self.timeout = 30
		# Boolean on whether or not to check for the physical 
		# process ID listening on the socket
		self.checkPID = True

	def startup(self):
		print 'initiating UNIXConnection'
		# Fire the hook displaying us as connecting to teh Asgard service
		self.fire('connecting')
		# Call the reactor to initialize the connection ...
		# ENERGIZING
		print 'Opening socket to: %s' % self.path
		self.connection = reactor.connectUNIX(address=self.path,
			factory=self.factory)
		print 'Energized!'