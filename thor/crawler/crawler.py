import os
import logging
from twisted.application import service
from twisted.internet.protocol import ClientFactory
from thor.application import server

class Crawler(service.MultiService):
    
    def __init__(self, host = '127.0.0.1', port = '21189'):
        self.logger = logging.getLogger('thor.crawler[%s]' % (os.getpid()))
        service.MultiService.__init__(self)
        
        self.connections = []
        self.threads = []
        self.spiders = []
        
        self.host = host
        self.port = port
        
        self.service = CrawlerService(self)
        
    def shutdown(self):
        self.logger.info('Initiating reactor shutdown process')
        from twisted.internet import reactor
        reactor.stop()
        self.logger.info('Reactor shutdown process completed - now exiting')
        sys.exit(2)


class CrawlerService(ClientFactory):
    
    def __init__(self, service, ip='127.0.0.1', port=21189):
        self.service = service
        self.logger = service.logger
        
        self.ip = ip
        self.port = port
    
    def startedConnecting(self, connector):
        self.logger.debug('Crawler service attempting to connect to host on <%s:%s>' %
            (self.ip, self.port))

    def buildProtocol(self, addr):
        self.logger.info('Crawler service established connection to host on <%s:%s>' %
            (self.ip, self.port))
            
        connection = server.Connection(self.service)
        self.service.connections.append(connection)
        
        return connection

    def clientConnectionLost(self, connector, reason):
        self.logger.info('Lost connection.  Reason: %s' % reason)
        self.logger.error('Lost connection.  Reason: %s' % reason)

    def clientConnectionFailed(self, connector, reason):
        self.logger.info('Connection failed.  Reason: %s' % reason)
        self.logger.error('Connection failed. Reason: %s' % reason)