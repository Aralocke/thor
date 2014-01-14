from thor.application import service
from thor.application.factories import unix

class UNIXConnection(service.Connection):
	def __init__(self, socket=None):
	    service.Connection.__init__(self)
	    # The path to the UNIX domain socket we need to connect to
	    self.path = socket
	    # We instantiate the factory here which will spawn our actual conenction to the server
	    self.factory = unix.UNIXClientFactory()

	def shutdownHook(self, shutdown):
		print '-> UNIXConnection shutdownHook -> %s' % self.getUID()
		shutdown.callback(None)

	def startupHook(self, startup):
		print '-> UNIXConnection startupHook -> %s' % self.getUID()
		startup.callback(None)