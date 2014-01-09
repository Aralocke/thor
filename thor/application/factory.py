from twisted.internet import protocol
from thor.common.identity import generate_uid

class ClientFactory(protocol.ClientFactory):
    def __init__(self):
        pass

class ServerClientFactory(protocol.ServerFactory):
    def __init__(self, protocol=None):
        # Referenced in the twisted Factory class. We create insatnces of this 
        # protocol in the buildProtocol method
        self.protocol = None
        # List of clients we are currently handling
        self.clients = {}
        # The UID gives us a unique identifier to keep track fo the service
        # that we are now running. This is referred to later and saved
        # as an index
        self.uid = generate_uid()

    def hasClients(self):
        if not self.clients:
            return False
        return True

    def startFactory(self):
        print '-> startFactory -> %s' % self.uid

    def stopFactory(self):
        print '-> stopFactory -> %s' % self.uid