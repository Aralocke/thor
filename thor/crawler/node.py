import logging
import os
import signal as sig
from twisted.internet import protocol

class Node(protocol.ProcessProtocol):
    
    def __init__(self, args=[], service=None):
        self.logger = logging.getLogger(__name__)
        self.args = args
        self.service = service
        
    def setParentService(self, service):
        self.service = service
        
    def setProcess(self, process):
        self.process = process
        
    def signal(self, signal):
        print 'signal %d received for PID %d' % (signal, self.pid)
        os.kill(self.pid, signal)
    
    def kill(self):
        os.kill(self.pid, sig.SIGKILL)        
    
    def connectionMade(self):
        self.pid, status = self.transport.pid, self.transport.status       
        
        self.logger.debug('New process connected from pid %s (%s)',
            self.pid, status)
        
    def outReceived(self, data):
        print "outReceived! with %d bytes!" % len(data)
        
    def childDataReceived(self, childFD, data):
        print 'PM -> %s' % (data)
        
    def errReceived(self, data):
        print "errReceived! with %d bytes!" % len(data)
        print 'PM -!-> %s' % data
        
    def inConnectionLost(self):
        print "PM  - inConnectionLost! stdin is closed! (we probably did it)"
        
    def outConnectionLost(self):
        print "PM  - outConnectionLost! The child closed their stdout!"
        
    def errConnectionLost(self):
        print "PM  - errConnectionLost! The child closed their stderr."
        
    def processExited(self, reason):
        
        _value = reason.value
        status, signal, exitCode = _value.status, _value.signal, _value.exitCode
        
        if exitCode is None:
            print "[%d] PM  - processExited - signal %s" % (self.pid, signal)
        else:
            print "[%d] PM  - processExited - code %s" % (self.pid, exitCode)
        
    def processEnded(self, reason):
        
        _value = reason.value
        status, signal, exitCode = _value.status, _value.signal, _value.exitCode
        
        if exitCode is None:
            print "[%d] PM  - processEnded - signal %s" % (self.pid, signal)
        else:
            print "[%d] PM  - processEnded - code %s" % (self.pid, exitCode)
        print "PM  - quitting"
        
        self.service.notifyNodeShutdown(self)