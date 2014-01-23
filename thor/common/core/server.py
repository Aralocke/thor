from twisted.internet import protocol
from thor.common.core import service

class Server(service.Service):

	factory = None

	def __init__(self, factory=None):
		# initialize the base service and the parent classes
		service.Service.__init__(self)
		# Save a reference to the factory that we will use to spawn ServerClients
		# from. This should be an instance that extends from twisted's built-in
		# twisted.internet.protocol.ServerFactory
		self.factory = factory or None
		# The server's run a number of plugins. These plugins are run on a trigger
		# system that gets registered by the implementing classes. A good example of this
		# is a PING/PONG server for maintaining network communications
		self.plugins = {}