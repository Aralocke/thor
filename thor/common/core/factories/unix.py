from thor.common.core import factory

class UNIXClientFactory(factory.ClientFactory):

    def __init__(self, parent, protocol):
        factory.ClientFactory.__init__(self, parent, protocol)

    def startedConnecting(self, connector):
    	print 'UNIXConnection is attempting to connect to socket'

	def clientConnectionFailed(self, connector, reason):
		print 'UNIXConnection has failed to connect to socket'
		print 'Reason: %s' % reason

	def clientConnectionLost(self, connector, reason):
		print 'UNIXConnection has lost connection to socket'
		print 'Reason: %s' % reason

class UNIXServerClientFactory(factory.ServerClientFactory):
    def __init__(self, parent, protocol):
        factory.ServerClientFactory.__init__(self, parent, protocol)