import os
import logging
from twisted.application import service
from twisted.internet import protocol
from thor.application import server

class CrawlerService(service.Service):
    
    def __init__(self, iface='127.0.0.1', port=21189):   
        self.ip = iface
        self.port = port
        
        self.factory = CrawlerConnectionFactory()
        
class CrawlerConnectionFactory(protocol.ClientFactory):
    
    def startedConnecting(self, connector):
        self.service.logger.debug('Crawler service attempting to connect to host on <%s:%s>' %
            (self.ip, self.port))

    def buildProtocol(self, addr):
        self.service.logger.info('Crawler service established connection to host on <%s:%s>' %
            (self.ip, self.port))
            
        connection = server.Connection(self.service)
        self.service.connections.append(connection)
        
        return connection

    def clientConnectionLost(self, connector, reason):
        self.service.logger.info('Lost connection.  Reason: %s' % reason)

    def clientConnectionFailed(self, connector, reason):
        self.service.logger.info('Connection failed.  Reason: %s' % reason)