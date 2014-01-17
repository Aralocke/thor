from twisted.internet import defer, reactor
from twisted.python import log
from thor.common import system as sys
from thor.common.core import servers, service
from thor.common.core.service import RUN_OPT_ASGARD, RUN_OPT_CRAWLER, RUN_OPT_WEB

class Asgard(service.DaemonService):

	def __init__(self, webServerOnly=False, **kwargs):
		# Run the init routines on the parent class
        # this sets up all of the Twisted logic needed
        # later on
		service.DaemonService.__init__(self, **kwargs)
		service.DaemonService.setName(self, 'Asgard')
		# Flag to signal our startup if we are only spawning a web server or if we are
		# a full Asgard instance. Web Servers will only spawn TCP servers capable of handling
		# the RESTful web service
		self.isWebServer = webServerOnly
		# After we know what run mode we are, we're going to handle parsing the args
		# that were passed to the application via kwargs
		#
		# Number of processes we're going to spawn. These are workers that respond to signals,
		# web tasks, etc and do the heavy labor
		self.processes = kwargs.get('processes', sys.processes())
		self.threads = kwargs.get('threads', sys.threads())
		# Location of the socket that will be created for communicating with the
		# local processes
		self.socket = kwargs.get('socket', None)
		# Hold references to the servers and child processes running under this 
		# serice. Asgard acts as a hub for all information in the server application.
		self.servers = {}
		self.nodes = {}
		# Set the actual listening interface variables here so that they exist
		# within the class - The default values are set below
		self.iface = { 'http' : '127.0.0.1', 'https' : '127.0.0.1' }
		self.port = { 'http' : 80, 'https' : 443 }
		# Handle processing of the listening interfaces
		#
		# By default we do not proceed if the transport option is not specified. This is
		# because by we create a default HTTP server regardless. But if iface or port are
		# specified we will use them
		self.setWebInterface('http', iface=kwargs.get('iface', None), 
			port=kwargs.get('port', None))
		# Web interface configuration for the HTTP transport protocol. By default this should
		# get blocked out if there iface/port settings are blank, and these settings are
		# blank as well
		# Web Service interface configuration for the HTTPS transport protocol.
		self.setWebInterface('https', iface=kwargs.get('ssl-iface', self.iface['https']), 
			port=kwargs.get('ssl-port', self.port['https']))

	def create_server(self, **kwargs):
		# All of the application servers exist in this import from here
		# we can manipulate them to spawn their factories and then their
		# specific protocols
		if kwargs.get('socket') is not None:
			# This will create a UNIX socket at the location of 'socket' and
			# listen for incomming connections form this location
			server = servers.UNIXServer( socket=kwargs.get('socket') )
		elif kwargs.get('docroot') is not None:
			# This tells us we are going to create a web server. The Web Server
			# will accept connections on the port/interface combo and return
			# web requests. The catch here is we want to support SSL and REGULAR
			# HTTP requests
			if kwargs.get('sslcert') is not None:
				# TODO Create a SSLWebServer socket
				return None
			else:
				# TODO Check if root directory exists
				# TODO WebServer Caching?
				server = servers.WebServer( root=kwargs.get('docroot'), 
					iface=self.iface['http'], port=self.port['http'] )
		else:
			# Create a standard TCP server that listens for incomming connections
			# on this interface/port combo. The receivers here will be instances
			# of the basic.LineReceiver class and respond to requests
			server = servers.TCPServer( iface=self.iface['http'], port=self.port['http'] )
		# We maintain an internal list of servers that we are watching in a list
		# for shutdowns and such this list will be interated through and every
		# server will drop it's connections on a graceful shutdown
		server.addHook('startup', self.registerServer, server)
		server.addHook('shutdown', self.removeServer, server)

		# The server represents a service that we store within our multiservice
		# so we need to set the parent service reference
		server.setServiceParent(self)

		# Return the server instance to whatever called it and continue on from
		# there.
		return server

	def getRunmode(self):
		if self.isWebServer:
			return RUN_OPT_WEB

		return RUN_OPT_ASGARD

	def registerServer(self, server):
		if server.getUID() in self.servers:
			raise KeyError('Server already exists')
		self.servers[server.getUID()] = server
		self.fire('server.register')

	def removeServer(self, server):
		if server.getUID() not in self.servers:
			raise KeyError('Server not registered')
		del self.servers[server.getUID()]
		self.fire('server.remove')

	def setWebInterface(self, transport='http', iface=None, port=None):
		# Only two web transport types. Maybe down the road we can implement
		# something else (like streaming?) but return an exception if it's not 
		# expected
		if transport not in ('http', 'https'):
			raise KeyError('Only available web transports are http and https')

		if iface is not None:
			self.iface[transport] = str(iface)

		if port is not None:
			self.port[transport] = int(port)

		# Only fire an event when there is an actual change during runtime
		if self.getState('RUNNING'):
			if port is not None or iface is not None:
				self.fire('web.interface.change')

	def shutdown(self):
		print 'Asgard shutdown hook'

	def startup(self):
		print 'Asgard startup hook'
		try:
			log.msg('Spawning local socket: %s' % self.socket)
			u_server = self.create_server(socket=self.socket)
			w_server = self.create_server(docroot='web')
		except:
			log.err()