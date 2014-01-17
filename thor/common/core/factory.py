from twisted.internet import protocol
from thor.common.core import object

class ClientFactory(object.Object, protocol.ClientFactory):

    def __init__(self):
        object.Object.__init__(self)

class ServerClientFactory(object.Object, protocol.ServerFactory):

    def __init__(self, protocol=None):
        object.Object.__init__(self)

    def startFactory(self):
        print '-> startFactory -> %s' % self.getUID()

    def stopFactory(self):
        print '-> stopFactory -> %s' % self.getUID()