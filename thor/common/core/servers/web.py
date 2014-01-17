import mimetypes
import os

from twisted.application import internet
from twisted.internet import defer, reactor
from twisted.web import static, server, vhost
from thor.common.core.servers import tcp
from thor.common.core.factories import web

class WebServer(tcp.TCPServer):

	def __init__(self, iface='0.0.0.0', port=21189, root=None):
		tcp.TCPServer.__init__(self)

		self.docroot = root
		self.factory = None

		self.iface = iface
		self.port = port

	def startup(self):

		root = static.File(self.docroot)
		self.factory = web.WebSite(root)

		self.socket = reactor.listenTCP(self.port, self.factory, interface=self.iface)

class SSLWebServer(WebServer):

	def __init__(self, iface='0.0.0.0', port='21189', root=None,
			sslcert=None, sslkey=None, sslchain=None):
		# Startup the init sequence for the web server first. We need the routines
		# within the WebServer class run first but they will call our init methods
		# once we override them in this class for SSL routines
		WebServer.__init__(self, iface=iface, port=port, root=root)

mimetypes.types_map[".ico"] = "image/vnd.microsoft.icon"