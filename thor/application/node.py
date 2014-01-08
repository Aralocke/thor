import logging
import signal

from twisted.application import internet
from twisted.internet import defer
from thor.application import service

class Node(service.BaseService):
	def __init__(self, cmd=None):
		service.BaseService.__init__(self)
		self.args = None
		
	def getArgs(self):
		cmd = []
		for i in range(len(self.args)):
		    if isinstance(self.args[i], list):
		        cmd[i] = ' '.join([str(x) for x in self.args[i]]) 
		    else: 
		        cmd[i] = self.args[i]
		return cmd

	def shutdownHook(self, shutdown):
	    print 'Node shutdownHook -> %s' % self.uid
	    shutdown.callback(None)

	def startupHook(self, startup):
	    print 'Node startupHook -> %s' % self.uid
	    startup.callback(None)