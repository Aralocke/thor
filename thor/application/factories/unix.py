from thor.application import factory

class UNIXClientFactory(factory.ClientFactory):
	def __init__(self):
		factory.ClientFactory.__init__(self)

	def initialize(self):
		print 'UNIXClientFactory started'

class UNIXServerClientFactory(factory.ServerClientFactory):
	def __init__(self):
		factory.ServerClientFactory.__init__(self)

	def initialize(self):
		print 'UNIXServerClientFactory started'