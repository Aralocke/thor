from twisted.protocols import basic

class ClientProtocol(protocol.Protocol):

	def connectionMade(self):
		print 'Client Connection Made'

class ServerClientProtocol(ClientProtocol):

	def connectionMade(self):
		print 'Server Connection Made'