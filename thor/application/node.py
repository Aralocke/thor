import logging
import os

from twisted.application import internet
from twisted.internet import defer, protocol, reactor
from thor.application import service
from thor.common.identity import generate_uid

class ProcessManager(protocol.ProcessProtocol):

	parent = None
	state = None

	def __init__(self):
		# The UID gives us a unique identifier to keep track fo the service
		# that we are now running. This is referred to later and saved
		# as an index
		self.uid = generate_uid()
		# We map our file descriptors and the callbacks we call in the event of
		# something happening. By default there are 3 FD's in, out, and error which
		# get mapped by default in any program. But we are able to map extra file
		# descriptors to allow our applications to accept incomming data differently
		#
		self.fd = {}
		# Default File Descriptors
		# fd 0 - incomming data (stdin)
		# fd 1 - outgoing data (stdout)
		# fd 2 - error data (stderr)
		self.mapFileDescriptor(0, self.inReceived,  self.inConnectionLost)
		self.mapFileDescriptor(1, self.outReceived, self.outConnectionLost)
		self.mapFileDescriptor(2, self.errReceived,  self.errConnectionLost)
		# Set the initial state of the application. This will also ensure there is
		# a default value upon final construction to refer to
		self.setState('INIT')
		# PID file for the current process we are attached to
		self.pid = 0

	def childDataReceived(self, childFD, data):
		# We need to filter the traffic to the callable functions based on the childFD
		# that we are given and what we have mapped. The default three should ALWAYS
		# exist becaus ethey are set at construction and not runtime
		if childFD not in self.fd:
			raise KeyError('childFD [%s] has not been mapped' % childFD)
		# The return value saved is a mixed tuple of the data we need 
		# (see mapFileDescriptior for more information). Overwriting childFD because the
		# expected values will be the same 
		childFD, callable, errCallable = self.fd[childFD]
		# call the function here. this is the data received functions which catch data
		# that has come in ove rthe pipes. We don't process error data here
		callable(data)

	def childConnectionLost(self, childFD):
		# We need to filter the traffic to the callable functions based on the childFD
		# that we are given and what we have mapped. The default three should ALWAYS
		# exist becaus ethey are set at construction and not runtime
		if childFD not in self.fd:
			raise KeyError('childFD [%s] has not been mapped' % childFD)
		# The return value saved is a mixed tuple of the data we need 
		# (see mapFileDescriptior for more information). Overwriting childFD because the
		# expected values will be the same 
		childFD, callable, errCallable = self.fd[childFD]
		# call the function here. this is the data received functions which catch data
		# that has come in ove rthe pipes. We don't process error data here
		errCallable()

	def connectionMade(self):
		self.setState('RUNNING')
		self.pid = self.transport.pid

	def errReceived(self, data):
		print '> errReceived -> %s' % data

	def getState(self):
		return self.state

	def inReceived(self, data):
		print '> inReceived -> %s' % data

	def mapFileDescriptor(self, childFD, function, errFunction, force=True):
		# Test that the receiving function we want is a callable function
		assert callable(function), "%s is not callable" % function
		# Test the error function to see if it is receivable
		assert callable(errFunction), "%s is not callable" % errFunction
		# By default we will overwrite the mthods we call if it already exists in
		# the map. DOn't see any reason NOT to over write, but it might be handy
		# somewhere down the line
		if force and childFD in self.fd:
			raise KeyError('File Descriptor is already mapped')
		# Setup the file descriptor map so that we can point the callable functions to
		# the right data streams
		self.fd[childFD] = (childFD, function, errFunction)
		# We return the values which were given to us
		return childFD, function, errFunction

	def outReceived(self, data):
		print '> outReceived -> %s' % data

	def processEnded(self, reason):
		self.setState('STOPPED')

	def processExited(self, reason):
		status, signal, exitCode = reason.value.status, reason.value.signal, reason.value.exitCode

		if exitCode is None:
			print "[%d] processExited - signal %s" % (self.pid, signal)
		else:
			print "[%d] processExited - code %s" % (self.pid, exitCode)
	
	def setParentService(self, parent):
		self.parent = parent

	def setState(self, state):
		print 'Changing state to: %s -> %s' % (state, self.uid)
		self.state = state

class Node(service.BaseService):

	def __init__(self, cmd=None):
		# Call the initialzation functions of the BaseService class. This will setup
		# our basic event handling, logging, etc
		service.BaseService.__init__(self)
		# These are the command line args we start our process with. The 0th element
		# will ALWAYS represent the python file that started the application. In most
		# cases this will be run.py. 
		self.args = cmd
		# We setup a ProcessManager which handles interacting with the Process we maintain.
		# It's a bit of a misnomer but the ProcessManager is more like a 'server client' 
		# than a factory. The client interacts with and is alerted to events and errors
		# within the process protocol
		self.manager = ProcessManager()
		self.manager.setParentService(self)
		# These are the general bits and pieces of information from the process. Each one
		# will remain during the lifetime of the process
		self.pid = None
		self.process = None

	def getArgs(self):
		cmd = []
		for i in range(len(self.args)):
			if self.args[i] is None:
				continue
			if isinstance(self.args[i], list):
				cmd.append(' '.join([str(x) for x in self.args[i]])) 
			else: 
				cmd.append(self.args[i])
		return cmd

	def shutdownHook(self, shutdown):
	    print '-> Node shutdownHook -> %s' % self.uid

	    self.signalProcess('INT')

	    shutdown.callback(None)

	def signalProcess(self, signal='INT'):
		print '-> signalProcess :: %s [%s] -> %s' % (signal, type(signal), self.uid)
		if isinstance(signal, str):
			if signal not in ('INT', 'KILL', 'TERM'):
				raise KeyError('Unknown signal string')

			try:
				if self.manager.getState() == 'RUNNING':
					self.process.signalProcess(signal)
			except Exception as e: 
				pass

		elif isinstance(signal, int):
			try:
				if self.manager.getState() == 'RUNNING':
					self.process.signalProcess(signal)
			except Exception as e: 
				pass
		else:
			raise KeyError('Unknown signal')

	def startupHook(self, startup):
	    print '-> Node startupHook -> %s' % self.uid
	    
	    args = self.getArgs()
	    self.manager.setState('SPAWNING')
	    self.process = reactor.spawnProcess(self.manager, args[0], args, usePTY=True)
	    self.fireEventTrigger('node.spawn')

	    startup.callback(None)