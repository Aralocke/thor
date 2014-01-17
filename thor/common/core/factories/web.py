from twisted.internet import reactor
from twisted.web import http, resource, server

class WebSite(server.Site):

	def __init__(self, path, protocol=None, requests=None, 
			timeout=60, *args, **kwargs):
		# We're creating a new website. Call the parent constructor and setup
		# the environment that we're going to be using
		server.Site.__init__(self, path, *args, **kwargs)