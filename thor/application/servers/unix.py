import logging
import random
import os

from twisted.application import internet
from twisted.internet import defer, reactor
from thor.application import server
from thor.application.factories import unix

class UNIXServer(server.Server):
    def __init__(self, socket=None, owner=None, group=None):
        server.Server.__init__(self, asgard=None)

        self.path = socket
        self.socket = None

        self.logger = logging.getLogger('thor.application.UNIXServer')

        self.factory = unix.UNIXServerClientFactory()

        self.owner = owner or os.getuid()
        self.group = group or os.getgid()

    def initialize(self):
    	print 'UNIXServer initialized -> %s' % self.uid

    def startupHook(self, startup):
        print 'UNIXServer startupHook called  -> %s' % self.uid
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
        self.logger.debug('Creating socket: %s' % self.path)
        self.socket = reactor.listenUNIX(self.path, self.factory)
        # After we create the listening socket, let's secure it by setting proper 
        # ownership and permissions on it
        os.chown(self.path, self.owner, self.group)
        # We're done setting up so we can callback and move on
        startup.callback(None)

    def shutdownHook(self, shutdown):
        print 'UNIXServer shutdownHook called  -> %s' % self.uid
    	shutdown.callback(None)