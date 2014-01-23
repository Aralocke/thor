import os

from twisted.application import internet
from twisted.internet import defer, process, protocol, reactor
from twisted.python import log, runtime

from thor.common.core import component, connection, service

class ProcGroupProcess(process.Process):

    def _setupChild(self, *args, **kwargs):
        Process._setupChild(self, *args, **kwargs)

        os.setpgid(0, 0)

class ProcessManager(component.Component, connection.BufferedConnection, 
    protocol.ProcessProtocol):

    parent = None

    def __init__(self, parent=None):        
        component.Component.__init__(self)
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

    def outReceived(self, data):
        print '> outReceived -> %s' % data

    def processEnded(self, reason):
        self.setState('STOPPED')

    def processExited(self, reason):
        status, signal, exitCode = reason.value.status, reason.value.signal, reason.value.exitCode

        if exitCode is None:
            log.msg('Crawler process [%d] exited - signal %s' % 
                (self.pid, signal))
        else:
            log.msg('Crawler process [%d] exited - code %s' % 
                (self.pid, exitCode))

        # By this point the process has exited and is no longer running. In most cases this
        # happened during a shutdown. However we need to shutdown the node which will in turn
        # alert asgard to a shutdown process
        self.parent.stopService()

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
        self.environment = None
        self.workdir = None
        self.usePTY = True
        self.owner = owner or os.getuid()
        self.group = group or os.getgid()

    def shutdown(self):
        # few things need to happen here.
        # 1) Given an actual shutdown of the node we only proceed if the node is running
        # We should not trigger a signaled shutdown if the process has shutdown already
        if self.manager.getState('RUNNING'):
            self.signalProcess(2)        
        # 2) We're not running or a premature shutdown happened, faulty process
        # rehash, whatever, for some reaosn the application is still running
        # and we are not


    def signalProcess(self, signal='INT'):
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

        log.msg('Initializing Crawler application [%s, %s]: %s' % 
            (self.owner, self.group, self.args))

        self.process = self.__spawnProcess(
            self.manager, self.args[0], self.args,
            self.environment, self.workdir,
            usePTY=self.usePTY)

        self.pid = self.process.pid

        self.fire('node.spawn')

    def __spawnProcess(self, processProtocol, executable, args=(), env={},
        path=None, uid=None, gid=None, usePTY=False, childFDs=None):
        # use the ProcGroupProcess class, if available

        return reactor.spawnProcess(processProtocol, executable, args,  
                env, path, usePTY=usePTY) 