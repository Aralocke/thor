from twisted.protocols import basic
from twisted.python import log
from thor.common.core import object

class ClientProtocol(object.Object, basic.LineReceiver):

	def __init__(self):
		object.Object.__init__(self)

	def connectionLost(self, reason):
		# We should notify someone .. or something that a connection 
		# has been quietly lost
		self.factory.parent.fire('disconnected')

	def connectionMade(self):
		self.factory.parent.fire('connected')
		self.sendLine('Established connection to the server')

	def lineReceived(self, line):
		print '-> %s' % line

class ServerClientProtocol(ClientProtocol):

	def __init__(self):
		ClientProtocol.__init__(self)

	def connectionMade(self):
		self.sendLine('Established connection from a client')
		self.factory.parent.fire('connected')

	def connectionLost(self, reason):
		# We need to remove ourselves form the parent factory's list of
		# clients
		del self.factory.clients[self.getUID()]
		# Also we should notify someone .. or something that a connection 
		# has been quietly lost. FOr now we will just print a message out
		ClientProtocol.connectionLost(self, reason)