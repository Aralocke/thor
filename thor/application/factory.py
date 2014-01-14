from zope.interface import implements
from twisted.internet import protocol
from thor.common.identity import generate_uid
from thor.common.scaffold import foundation

class ClientFactory(protocol.ClientFactory):

    implements(foundation.IIdentifiable)

    def __init__(self):
        # The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
        self.__uid = generate_uid()
        # Referenced in the twisted Factory class. We create insatnces of this 
        # protocol in the buildProtocol method
        self.protocol = None

    def getUID(self):
        return self.__uid

class ServerClientFactory(protocol.ServerFactory):
    
    implements(foundation.IIdentifiable)

    def __init__(self, protocol=None):
        # The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
        self.__uid = generate_uid()
        # Referenced in the twisted Factory class. We create insatnces of this 
        # protocol in the buildProtocol method
        self.protocol = None
        # List of clients we are currently handling
        self.clients = {}

    def getUID(self):
        return self.__uid

    def hasClients(self):
        if not self.clients:
            return False
        return True

    def startFactory(self):
        print '-> startFactory -> %s' % self.getUID()

    def stopFactory(self):
        print '-> stopFactory -> %s' % self.getUID()