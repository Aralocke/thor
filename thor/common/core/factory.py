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