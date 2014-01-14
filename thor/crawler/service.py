import logging 

from twisted.internet import defer, reactor
from thor.application import service
from thor.application.connections import unix

class Crawler(service.DaemonService):

    def __init__(self, threads=None, socket=None):
        # Run the init routines on the parent class
        # this sets up all of the Twisted logic needed
        # later on
        service.DaemonService.__init__(self, daemon=True)
        service.DaemonService.setName(self, 'Crawler')
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Crawler')
        # We need to save a reference to the socket that we connect to for management
        # updates on the local system. This socket is managed by the Asgard process
        # on the local machines
        self.path = socket
        # We start a UNIXConnection to represent our link to the main service. This will
        # handle the protocol level operations of the network and split protocol logic 
        # from our service logic here
        self.connection = None
        # We maintain a list of our spider pool
        self.spiders = {}

    def create_connection(self, path=None):
        path = path or 'data/thor.sock'

        connection = unix.UNIXConnection(socket=path)
        connection.setParentService(self)

        reactor.callFromThread(connection.startup)       

        return connection

    def shutdownHook(self, shutdown):
        print 'Crawler shutdownHook called'
        # Any crawler specfic shutdown code should happen here. We don't callback the
        # hook until after the connection has processed and shut itself down. This will
        # ensure all traffic is processed appropriately
        shutdownResults = []

        # The shutdownHook for the Crawler is run through to the shutdown of the 
        # connection to the Asgard service. This means that the shutdowns are linked
        # and we use the callback from the shutdownHook of UNIXConnection as our 
        # usual trigger here
        if self.connection is not None:
            try:
                result = self.connection.shutdown()
            except Exception as e:
                print 'ERROR IN shutdownHook(servers) [Crawler] -> %s' % e
            else:
                if isinstance(result, defer.Deferred):
                    shutdownResults.append(result)        

        # Finally we chain the services deferred to our deferred here. When we have no more
        # services left to shutdown we well execute the call back and shut down the entire service 
        if shutdownResults:     
            d = defer.gatherResults(shutdownResults, consumeErrors=True)
            d.addCallback(shutdown.callback)

        # Backup plan scenario in case the connection has already collapsed
        if not self.connection and not self.spiders:       
            shutdown.callback(None)

    def startupHook(self, startup):
        print 'Crawler startupHook called'
        # We must initiate a connection to the local management interface socket.
        # This socket allows us to communicate with our parent process and receive
        # notifications regarding tasks and other I/O operations
        self.connection = self.create_connection()
        startup.callback(None)
        