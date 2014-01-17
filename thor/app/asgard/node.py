import os

from twisted.application import internet
from twisted.internet import defer, protocol, reactor

from thor.common.core import component, service

class ProcessManager(component.BufferedComponent, protocol.ProcessProtocol):

    parent = None
    state = None

    def __init__(self, parent=None):
        component.BufferedComponent.__init__(self)
        # Save a reference to our parent node controllers
        self.parent = parent
        # Set the initial state of the application. This will also ensure there is
        # a default value upon final construction to refer to
        self.setState('INIT')
        # PID file for the current process we are attached to
        self.pid = 0

    def connectionMade(self):
        self.setState('RUNNING')
        self.pid = self.transport.pid

    def errReceived(self, data):
        print '> errReceived -> %s' % data

    def inReceived(self, data):
        print '> inReceived -> %s' % data

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

class Node(service.Service):

    def __init__(self, cmd=None, owner=None, group=None):
        # Call the initialzation functions of the BaseService class. This will setup
        # our basic event handling, logging, etc
        service.Service.__init__(self)
        # These are the command line args we start our process with. The 0th element
        # will ALWAYS represent the python file that started the application. In most
        # cases this will be run.py. 
        self.args = cmd
        # We setup a ProcessManager which handles interacting with the Process we maintain.
        # It's a bit of a misnomer but the ProcessManager is more like a 'server client' 
        # than a factory. The client interacts with and is alerted to events and errors
        # within the process protocol
        self.manager = ProcessManager(self)
        # These are the general bits and pieces of information from the process. Each one
        # will remain during the lifetime of the process
        self.pid = None
        self.process = None

        self.owner = owner or None
        self.group = group or None

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

    def shutdown(self):
        print '-> Node shutdownHook'
        self.signalProcess(2)

    def signalProcess(self, signal='INT'):
        print '-> signalProcess :: %s [%s] -> %s' % (signal, type(signal), self.getUID())
        if self.pid is not None:
            if isinstance(signal, str):
                if signal not in ('INT', 'KILL', 'TERM'):
                    raise KeyError('Unknown signal string')

                try:
                    if self.manager.getState() in ('RUNNING', 'STOPPING'):
                        self.process.signalProcess(signal)
                except Exception as e: 
                    pass

            elif isinstance(signal, int):
                try:
                    if self.manager.getState() in ('RUNNING', 'STOPPING'):
                        self.process.signalProcess(signal)
                except Exception as e: 
                    pass

            else:
                raise KeyError('Unknown signal')

    def startup(self):            
        self.manager.setState('SPAWNING')
        print 'Executing [%s, %s]: %s' % (self.owner, self.group, self.args)
        self.process = reactor.spawnProcess(self.manager, self.args[0], self.args,  
            uid=self.owner, gid=self.group)

        self.pid = self.process.pid

        self.fire('node.spawn')