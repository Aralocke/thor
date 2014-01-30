from twisted.internet import protocol
from thor.common.core import object

class ClientFactory(object.Object, protocol.ClientFactory):

	parent = None

	def __init__(self, parent, protocol):
		object.Object.__init__(self)
		# The parent value represents the connection object that the
		# factory creates protocol clients for
		self.parent = parent
		# The protocol we will spawn in the event of a connection. This is a 
		# single protocol to understand communications between the Asgard
		# server and the crawlers
		self.protocol = protocol

	def startedConnecting(self):
		# Fire the hook displaying us as connecting to the Asgard service
		self.parent.fire('connecting')

class ServerClientFactory(object.Object, protocol.ServerFactory):

	parent = None

	def __init__(self, parent, protocol):
		object.Object.__init__(self)
		# The parent value represents the server that we are creating
		# protocol clients for
		self.parent = parent
		# The protocol we will spawn in the event of a connection. This is a 
		# single protocol to understand communications between the Asgard
		# server and the crawlers
		self.protocol = protocol
		# We maintain a list of the connections we produce stored by their
		# object UID
		self.clients = {}

	def buildProtocol(self, addr):
		# Create the client and pass it a reference to ourselves
		# the factory
		client = self.protocol()
		client.factory = self
		# We need to do book keeping on the client and keep track of
		# the connections we produce
		self.clients[client.getUID()] = client
		# AFter we do some basic book keeping we return the protocol object and 
		# and continue on our way
		return client