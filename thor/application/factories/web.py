from twisted.internet import reactor
from twisted.web import http, resource, server

# Modified based on the TimeoutHTTPChannel from the QWebIRC package
class TimeoutHTTPChannel(http.HTTPChannel):

	def __init__(self, timeout=60):
		# Call the parent constructor to setup the HTTP channel for us
		# it is undocumented however there is code we will need for execution
		http.HTTPChannel.__init__(self)
		# Giove ourselves a timeout before we forcibly close the HTTP channel
		# we are currently using
		self.timeout = timeout
		# Deferred that will be fired when the custom timeout has reached
		# it's point and we fire the reactor timer
		self.customTimeout = None

	def connectionMade(self):
		if self.timeout:
		    self.customTimeout = reactor.callLater(self.timeout, self.timeoutOccured)
		http.HTTPChannel.connectionMade(self)

	def timeoutOccured(self):
		self.customTimeout = None
		self.transport.loseConnection()

	def cancelTimeout(self):
		if self.customTimeout is not None:
			try:
				self.customTimeout.cancel()
				self.customTimeout = None
			except error.AlreadyCalled:
			    pass

	def connectionLost(self, reason):
		self.cancelTimeout()
		http.HTTPChannel.connectionLost(self, reason)

class RootResource(resource.Resource):
	pass

class WebSite(server.Site):

	def __init__(self, path, protocol=None, requests=None, timeout=60, *args, **kwargs):
		# We're creating a new website. Call the parent constructor and setup
		# the environment that we're going to be using
		server.Site.__init__(self, path, *args, **kwargs)
		# Like any factory the protocol we're using is how we are goign to handle
		# any client interaction across the HTTP channel
	#self.protocol = protocol or TimeoutHTTPChannel
		# TO preserve resources we use a Timeout channel
		self.timeout = timeout

	#def buildProtocol(self, addr):
	#	p = TimeoutHTTPChannel(self.timeout)
	#	return p