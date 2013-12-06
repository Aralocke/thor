import logging
from twisted.internet import protocol

class ProcessManager(protocol.ProcessProtocol):
    
    def __init__(self, service):
        self.logger = logging.getLogger(__name__)
        self.service = service
        
    def _accounting(self):
        self.service._accounting()
    
    def connectionMade(self):
        pid, status = self.transport.pid, self.transport.status
        
        self.logger.debug('New process connected from pid %s (%s)',
            pid, status)
        
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
        print "PM  - processExited, status %d" % (reason.value.exitCode)
        
    def processEnded(self, reason):
        print "PM  - processEnded, status %d" % (reason.value.exitCode)
        print "PM  - quitting"