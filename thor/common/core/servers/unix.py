import os

from twisted.internet import defer, reactor
from thor.common.core import server
from thor.common.core.factories import unix

class UNIXServer(server.Server):

	def __init__(self, socket=None, protocol=None,
			owner=None, group=None):

		server.Server.__init__(self)

		self.path = socket
		self.socket = None

		self.factory = unix.UNIXServerClientFactory(self, protocol)

		self.owner = owner or os.getuid()
		self.group = group or os.getgid()

	def startup(self):
		# When working with local sockets we need to test the socket for a few
		# security measures and verification tests
		#
		# First test is to verify that the socket is not null and if it is use
		# our default, which is to save it in the data directory
		if self.path is None:
			randomizer = str(int(os.getpid()) * int(random.random() * 1000))
			self.path = 'data/thor.%s.sock' % (randomizer)
		# If the data directory does not exist, create it now
		if not os.path.exists('data'):
			os.mkdir('data')
		# if the socket ALREADY exists in the datadir remove it now. This really 
		# should never happen, it's what a 1-65535 chance? if this happens, buy
		# a lottery ticket or two (lol)
		if os.path.exists(self.path):
			os.unlink(self.path)
		# Now that we have a socket we can make the actual listening socket
		self.socket = reactor.listenUNIX(self.path, self.factory)
		# After we create the listening socket, let's secure it by setting proper 
		# ownership and permissions on it
		os.chown(self.path, self.owner, self.group)