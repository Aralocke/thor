import logging
import os
import signal
import sys

from twisted.application import internet, service
from twisted.internet import defer, reactor

class Asgard(service.MultiService):
    
    _systemShutdown = None
    _serversShutdown = None
    _nodesShutdown = None
    
    def __init__(self, processes=-1, threads=-1, iface='0.0.0.0', port='21189'): 
        # Initialize the Multi Service
        service.MultiService.__init__(self)
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Asgard')
        
        # This controls the number of child processes spawned on creation. The 
        # reactor will call the spawn_* method for children processes on startup.
        # This value is found in the initial options command line.
        from thor.common.utils import system_data
        _processes, _threads = system_data()
        
        if processes == -1:
            self.processes = _processes
        else:
            self.processes = processes
            
        if threads == -1:
            self.threads = _threads
        else:
            self.threads = threads
        
        self.started = False
        self.system = 'Asgard'
        
        # Hold references to the servers and child processes running under this 
        # serice. Asgard acts as a hub for all information in the server application.
        self.servers = {}
        self.nodes = {}
        
        # Set the port and interface combination for the local listening socket
        # that the child processes should connect to
        self.setListeningInterface( iface=iface, port=port )
        
    def _cbStartup(self, result):
        # This callback really starts the service by setting the service status
        # variable and igniting the service parent classes        
        self.started = True
        
        # Quick debug message to let us know we started properly
        self.logger.debug('Startup sequence completed')
        
        # Here we start the parent classes 
        service.MultiService.startService(self)
        
        # Return the result from the callback chain and get outta dodge
        return result

    def _ebStartup(self, failure):
        # This errback shuts us down if an error occured in process pool startup
        
        # Log messages here to know about the failure and then shut down the 
        # reactor before anythign else can start up
        #
        # TODO Handle failures and provide better catastrophe logs
        self.logger.info("failure starting service: %s" % (str(failure)) )
        self.logger.error("stopping reactor due to failure...")
        
        # The mains erviuce failed to start, we're now down and getting
        # out of here
        reactor.stop()
        
        # Some kind of world ending error just happened here. If the logs appear 
        # useful, please tell somebody who knows what they are doign with this
        # application
        
    def allNodesShutdown(self):
        # Return the deferred that we fire when the server has been completely 
        # shutdown. This will not fire until all connections have been closed
        if self._serversShutdown is not None:
            return self._serversShutdown
        
        # We're not shutting down, so just return a deferred that says we did
        # whatever options we've been asked of and hope for this best
        return defer.succeed(True)
        
    def allServersShutdown(self):
        # Return the deferred that we fire when the server has been completely 
        # shutdown. This will not fire until all connections have been closed
        if self._nodesShutdown is not None:
            return self._nodesShutdown
        
        # We're not shutting down, so just return a deferred that says we did
        # whatever options we've been asked of and hope for this best
        return defer.succeed(True)

    def create_node(self, threads=-1, iface='127.0.0.1', port=21189, **options):
        # An array holding the arguments to send to the remote process
        # the first is the run.py command which will execute the node
        cmd = [ sys.argv[0] ]

        # Append the run mode option to the command line
        cmd.append(['-m', '2'])

        # Add the host and port that the Crawler node should connect too
        cmd.append(['-i', iface])
        cmd.append(['-p', port])
        
        # Append the number of threads to spawn
        if threads == -1:
            cmd.append(['-t', self.threads])
        else:
            cmd.append(['-t', threads])
            
        # Loop through the dictionary of arguments and process them as needed
        for option, value in options.iteritems():
            # If we are in debug mode, pass the debug flag to
            # all spawned children
            if option == 'debug' and value:
                cmd.append('-d')
                
        from thor.crawler import node
        node = node.Node( cmd, service=self )        

        # Now that the command has been built we'll implode the set
        # and pass it to spawn process
        for i in range(len(cmd)):
            if isinstance(cmd[i], list):
                cmd[i] = ' '.join([str(x) for x in cmd[i]]) 
        
        process = reactor.spawnProcess(node, cmd[0], cmd, usePTY=True)
        node.setProcess(process)
        
        self.nodes[process.pid] = node
        
        return node
        
    def create_server(self, iface='0.0.0.0', port='21189'):
        # Log message for the creation of a new server
        self.logger.debug('Creating new server listening on %s:%s', 
            iface, port)
        
        from thor.application import protocol
        server = protocol.Server( self, iface=iface, port=port )
        
        # Add the newly spawned server to the reactor (which is live) and
        # begin listening for connections on it.
        # Keep a refence to the socket that the server is listening on
        server.service = internet.TCPServer(port, server, interface=iface)
        server.service.setServiceParent(self)
        
        # Call the startup routines on the server we are initializing. The factory
        # acts a sthe persistent memory cache for the server and will contain
        # it's actual persistent logic
        reactor.callFromThread(server.startServer)
        
        # We maintain an internal list of servers that we are watching in a list
        # for shutdowns and such this list will be interated through and every
        # server will drop it's connections on a graceful shutdown
        self.servers[server.uid] = server
   
        return server
        
    def initialize(self):
        # This section is called before the reactor has initialized giving us 
        # the opportunity to create or link any code that will not be part of 
        # the reactor or should be part of the reactor on initialization before 
        # we create any of the servers or children nodes
        #
        # tl:dr - Insert pre-startup initialization code here
        pass
    
    def notifyServerShutdown(self, server):
        if server.uid in self.servers:     
            del self.servers[server.uid]
            
        return self._completeShutdown()
            
    def notifyNodeShutdown(self, node):
        if node.pid in self.nodes:
            del self.nodes[node.pid]
            
        return self._completeShutdown()
            
    def _completeShutdown(self):
        # Do not proceed if we are not engaging in a shutdown operation
        # This object will only be set in the event of a shutdown and
        # we should not proceed otherwise
        if self._systemShutdown is None: return 1      
        
        # Do not continue processing if we still have nodes that have not shutdown
        # This could be form nodes shutting down after scaling down, this will 
        # prevent a false shutdown
        if self.nodes: return 2
        
        # Calling this chain will result in shutting down of all the servers
        # once all the nodes have been closed. Waiting for nodes to shutdown
        # allows us to receive any final processing information from the nodes
        # connections      
        self._systemShutdown.addCallback(self._shutdown)       
        self._systemShutdown.callback(None)
        
        return 3
    
    def _shutdown(self, d):
        # This function gets called last in the deferred's shutdown chain. By this
        # point, all connections and servers have been successfully stopped, and
        # shotdown so we can shutdown the reactor when ready
        #
        # The application will stop the reactor and the main thread will exit
        # the execute method within run.py
        reactor.stop()
    
    def shutdown(self): 
        # We have no servers so we can return a simple deferred immeadietly and
        # not go to any other logic
        #
        # Only time this really could occur is if we have a zombie process or
        # one that failed to shutdown properly
        if not self.servers and not self.nodes:
            return defer.succeed(None)
        
        # We're initiating a shutdown so we setup the deferred chain that will
        # be returned. This chain will only fire after every server and node have
        # been shutdown and will prevent the reactor from exiting until we have
        # finished processing everything
        if self._systemShutdown is None:
            self._systemShutdown = defer.Deferred()       
        
        if self._serversShutdown is None:
            self._serversShutdown = defer.Deferred()   
            
        if self._nodesShutdown is None:
            self._nodesShutdown = defer.Deferred()
                
        # Logical check against the shutdown trigger being called twice. This call
        # will shutdown the service, all servers, and all nodes by executing
        # the shutdown sequence. It will be followed with the reactor shutting down
        # and the program exiting
        if self.started:
            self.logger.debug('Shutdown sequence initiated')
            reactor.callFromThread(self.stopService)
                
        return self._systemShutdown
    
    def setListeningInterface(self, iface='0.0.0.0', port='21189'):
        self.host = iface
        self.port = port
        
    def startService(self): 
        d = self.startDeferred = defer.Deferred()
        # Call the parent function first to setup the co-routines used by the 
        # rest of the service BEFORE we implement our own servers
        service.MultiService.startService(self)
        # Debug log message that the service has begun processing
        self.logger.debug('Starting the Asgard service')       
        
        # The following methods allow for a startup hook to be called when the 
        # startup is successful or when an error has occured
        d.addCallback(self._cbStartup)
        d.addErrback(self._ebStartup)
        # Ignite the reactor and begin the service
        # The startupHook will be the entry point to the internal server(s) and
        # components of the service
        reactor.callWhenRunning(self.startupHook, d)       
        
    def startupHook(self, startServiceDeferred):
        # Perform additional startup tasks.
        # This is a placeholder for future extension.
        # This function *MUST* callback / errback
        # the startServiceDeferred.
        #        
        # The application requires a single server running for child processes
        # to connect to. This is the only default required server that must
        # be running but the Asgard application is capable of managing many 
        # servers
        server = self.create_server( iface=self.host, port=self.port )
        self.logger.info('Primary listening server setup on <%s:%s>' % 
            (server.iface, server.port))
        
        #  Now we create the processes that act as the Crawlers
        for i in range(self.processes):
            node = self.create_node(threads=self.threads, iface=self.host, 
                port=self.port, debug=True)            
        
        startServiceDeferred.callback(True)
        # Returns None
        
    def shutdownHook(self):
        d = defer.Deferred()
        # Perform additional shutdown tasks.
        # For now this is just a placeholder for future extension.       
        return d
        
    def stopService(self):
        # Debug log message signalling the shutdown of the Asgard service
        self.logger.debug('Stopping the Asgard service')
        
        # After this point we begin shutting down all of the services in our
        # application gracefully and waiting on sockets to shut down properly
        status = service.MultiService.stopService(self)
        
        # Initiate the shutdown of the nodes by sending an interrupt signal
        # to each one. The signal will initate a sequence to exit out gracefully
        # and shut down all of their respective spiders
        for pid, node in self.nodes.iteritems():
            self.logger.debug('Sending shutdown signal to node on PID %s' % pid)
            reactor.callFromThread(node.signal, signal.SIGINT)     
            
        for uid, server in self.servers.iteritems():           
            if server.isActive():
                reactor.callFromThread(server.shutdown)
            
        # Shutdown the service permenantly by setting this flag. There is a possible
        # chance that the reactor shutdown trigger might go off again so this
        # will prevent two calls to reactor.stop()
        if self.started:
            status.chainDeferred(self.shutdownHook())
        self.started = False

        # Stop service returns a deferred or a None value in this case
        # we actually wait until the shutdown has completed to initialize a 
        # graceful shutdown of the application
        return status      
        
class Crawler(service.MultiService):
    
    _systemShutdown = None    
    
    def __init__(self, threads=-1, iface='127.0.0.1', port='21189'): 
        # Initialize the Multi Service
        service.MultiService.__init__(self)
        # Initiate the logger. This acts as the default logger for the 
        # application namesapce. Service level components will pass their log 
        # messages through this namespace
        self.logger = logging.getLogger('thor.application.Crawler [%s]' % os.getpid())
        
        # This controls the number of child processes spawned on creation. The 
        # reactor will call the spawn_* method for children processes on startup.
        # This value is found in the initial options command line.
        from thor.common.utils import system_data
        _processes, _threads = system_data()
            
        if threads == -1:
            self.threads = _threads
        else:
            self.threads = threads
        
        self.started = False
        self.system = 'Crawler'
        
        self.crawlers = {}
        
        # Set the port and interface combination for the local listening socket
        # that the child processes should connect to
        self.setManagementInterface( iface=iface, port=port )
        
    def initialize(self):
        self.logger.info('Initializing crawler application running on pid %s' % os.getpid())
        
    def setManagementInterface(self, iface='0.0.0.0', port='21189'):
        self.host = iface
        self.port = port
        
    def startService(self): 
        d = self.startDeferred = defer.Deferred()
        # Call the parent function first to setup the co-routines used by the 
        # rest of the service BEFORE we implement our own servers
        service.MultiService.startService(self)
        # Debug log message that the service has begun processing
        self.logger.debug('Starting the Crawler service')       
        
        def callback(result):
            # Return the result from the callback chain and get outta dodge
            return result
        
        def errback(err):
            pass
        
        # The following methods allow for a startup hook to be called when the 
        # startup is successful or when an error has occured
        d.addCallbacks(callback, errback)
        # Ignite the reactor and begin the service
        # The startupHook will be the entry point to the internal server(s) and
        # components of the service
        reactor.callWhenRunning(self.startupHook, d)       
        
    def startupHook(self, startServiceDeferred):
        # Perform additional startup tasks.
        #     
        # This callback really starts the service by setting the service status
        # variable and igniting the service parent classes        
        self.started = True
        # Quick debug message to let us know we started properly
        self.logger.debug('Startup sequence completed')
        # This function *MUST* callback / errback
        # the startServiceDeferred.
        startServiceDeferred.callback(True)
        # Returns None
    
    def _completeShutdown(self):
        if self._systemShutdown is None: return 1
        
        if self.crawlers: return 2
  
        self._systemShutdown.addCallback(self._shutdown)       
        self._systemShutdown.callback(None)
        
        return 3
    
    def _shutdown(self, d):
        reactor.stop()
    
    def shutdown(self):
        
        if self._systemShutdown is None:
            self._systemShutdown = defer.Deferred()
        
        if self.started:
            self.logger.debug('Shutdown sequence initiated')
            reactor.callFromThread(self.stopService)
                
        return self._systemShutdown
    
    def shutdownHook(self):
        d = defer.Deferred()
        print 'Crawler shutdown hook'
        return d
    
    def stopService(self):
        # Debug log message signalling the shutdown of the Asgard service
        self.logger.debug('Stopping the Crawler service')
        
        # After this point we begin shutting down all of the services in our
        # application gracefully and waiting on sockets to shut down properly
        status = service.MultiService.stopService(self)
        
        if not self.crawlers:
            self._completeShutdown()
        else:
            for id, crawler in self.crawlers:
                crawler.shutdown()
                
        if self.started:
            status.chainDeferred(self.shutdownHook())
        self.started = False
        
        # Stop service returns a deferred or a None value in this case
        # we actually wait until the shutdown has completed to initialize a 
        # graceful shutdown of the application
        return status
        
def allConnectionsClosed(protocol):
    from twisted.internet.defer import succeed
    
    # If the ProtocolFactory has implemented allConnectionsClosed we return the
    # deferred object here and wait until it fires. This chains a graceful 
    # shutdown via the reactor event system
    if hasattr(protocol, 'allConnectionsClosed'):
        return protocol.allConnectionsClosed()
    
    # If the factory has NOT implemented a graceful shutdown, we return a Deferred
    # object that has "succeeded"
    return succeed(None)