import os
import logging
import signal
import sys

# Setup the extended paths for the applications and includ ethe sources
# directory within our application namespace
absolute_path = os.path.abspath(__file__)
possible_topdir = os.path.normpath(os.path.join(absolute_path, os.pardir))

# Add the application path if it exists on to the main system path
if os.path.exists(os.path.join(possible_topdir, 'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

# Determine reactor type. Most *UNIX systems will use a poll based reactor
# while older systems will still user the select type
if os.name == 'nt':
    DEFAULT_REACTOR = 'select'  
else:
    DEFAULT_REACTOR = 'poll'

# Setup the command line option parser
from optparse import OptionParser
parser = OptionParser()

# The only universally default options that will be used for any incarnation
# of the application. The reactor selector and debug mode are all cross version 
# and the different incarnations all use them
parser.add_option('-d', '--debug', 
    help='Run in the Python Debugger.', 
    action='store_true', dest='debug', default=False)
parser.add_option('-r', '--reactor', 
    help='Which reactor to use (see --help-reactors for a list).', 
    dest='reactor', default=DEFAULT_REACTOR)

# Import the application functions to determine the safe number of threads and 
# child processes to spawn. These can be overriden with the command line parameters
# but by default we limit children to 1 per physical CPU core, and 4 threads per
# core
from thor.common.utils import system_data
processes, threads = system_data()

# These options are heavily dependent on the operating mode we are currently 
# running in. The options controlling children is used specifically for the 
# default maximum worker processes, and threads relate to the maximum default
# number of trheads that each process can run
parser.add_option('-t', '--threads', 
    help='', # TODO Help line 
    type='int', dest='threads', default=threads)
parser.add_option('-c', '--children', 
    help='', # TODO Help line
    type='int', dest='children', default=processes)
    
# The operable runmode constants
RM_SERVER = 1 # Run as a full server application
RM_NODE   = 2 # Run as a child node process
# The default run mode is to start as a server
DEFAULT_RUNMODE = RM_SERVER

# Here we determine the type of run mode to use. By default we will spawn an
# application that will start a listening server and N sub processes. These
# processes will on startup spawn a number of worker threads and enter a 
# waiting phase to begin processing
parser.add_option('-m', '--runmode', 
    help='', # TODO Help line
    type='int', dest='runmode', default=DEFAULT_RUNMODE)
    
# Determine what interfaces and port to run on. This gets handled differently 
# based on the runmode being
parser.add_option('-i', '--host', 
    help='', 
    type='string', dest='host', default='127.0.0.1')
parser.add_option('-p', '--port', 
    help='', 
    type='int', dest='port', default=21189)
parser.add_option('-s', '--socket', 
    help='Path to the socket that the Crawlers will conenct to or the Asgard process will spawn', 
    type='string', dest='socket', default='data/thor.sock')
    
# The args from 1- are all of the program arguments. The first arg (0th) is the
# program executable and thus useless to us in parsing
sargs = sys.argv[1:]

# Parse the options
(options, args) = parser.parse_args(args=sargs)

# Initiate the application logger. Now that we have begun parsing the arguments
# we'll use the logger to pass any errors or configuration issues that we find
LOG = logging.getLogger(__name__)

# Global service object. Depending on runmode this will be something different
# but will still have the same basic methods and callbacks
service = None

# Array of parsed arguments.
# This gets passed during execution to the final service components
args = []

# Default logging level is INFO messages only unless we are in debug mode.
LOG_LEVEL = logging.INFO

# We're triggering debug mode which is a LOT of extra information about the 
# ongoing processes and their activities. We also log a lot of extra infomration 
# to the log file and will force it to fill up a lot of data really fast
if options.debug:
    # The -b flag is used by the wtistd application to force no daemonization
    # It's kept here for the eventual implementation of twistd as the daemon
    # process manager later on
    args.append('-b')
    # Set the default log level to debug in all loggers globally. At this point
    # no other logger has been instantiated si the settings set here are 
    # effectively the default setings
    LOG_LEVEL = logging.DEBUG

# Setup the basic logging configuration. This sets a default format and a timestamp 
# prefixing all of the log messages. The file by default will appear in the root 
# of the project directory with a default log level
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s -- %(message)s',
    datefmt='[%I:%M:%S %p]', filename='thor.log', level=LOG_LEVEL)

# Basic infomration on the startup routines
LOG.info('Application started on pid %s', os.getpid()) 

# initialize the default reactor
reactor = options.reactor + 'reactor'
if options.reactor != DEFAULT_REACTOR:     
    getattr(__import__("twisted.internet", fromlist=[reactor]), reactor).install() 
    
# Debug log the reactor type being used
LOG.debug('Application reactor type: %s' % reactor)
    
def execute(app, argv, options):
    global service
    # When twistd is implemented the arguments passed to this function will
    # be a list that should be appended to the application arguments that
    # are passed to the twistd reactor. 
    #
    # The arguments used exclusively by THIS application will be parsed out
    # and saved in the options paramters
    args = [ sys.argv[0] ]
    if argv is not None:
        args.extend(argv)
    sys.argv = args 

    # Debugging purposes only to track the final argument list passed to the
    # twistd application
    LOG.debug('Application arguments: %s', sys.argv)
    
    # Instantiate the service object but building ourservles around a server
    # or two powered by Asgard. The Asgard service acts as a hub of information
    # for a number of servers and child nodes, all powered by the reactor
    if options.runmode == RM_SERVER:        
        # We imported the Asgard main service
        # for now we don't have any configuration options
        # but we will still return a created object here
        #
        #from thor.application import service as application
        from thor.application import asgard as application
        service = application.Asgard( processes=options.children )
        service.setListeningInterface( iface=options.host, port=options.port )
        
    elif options.runmode == RM_NODE: 
        # We import the service and setup the base MultiService for our application
        # In this runmode we are acting as a Crawler manager which manages the spiders
        # that are spawned in a thread pool
        from thor.crawler import service as application
        service = application.Crawler( threads=options.threads, socket=options.socket )
        # The management interface here is the connection we want to target to
        # connect to our parent asgard process. The host and port combination
        # are given to us at runtime when Asgard spawns the child
        #service.setManagementInterface( iface=options.host, port=options.port )
    
    else: 
        # We are passed a runmode in the options parser. This mode tells us how 
        # we will instantiate ourselves. Rather than assume we are a spawning 
        # server, the default behavior is to exit out and send an error
        LOG.error('Unknown runmode given [%s]' % (options.runmode))
        sys.exit(0)
    
    from twisted.internet import reactor
    # Connect our service to our application
    service.setServiceParent(app)

    # With the service object, we will use the reactor's callbacks to init and 
    # spawn the components of the application. Given the runmode we're using
    # this behavior could be different

    reactor.addSystemEventTrigger('after', 'startup', 
        service.startService)
    reactor.addSystemEventTrigger('after', 'startup', 
        service.startup) # This will initialize the service

    #reactor.addSystemEventTrigger('before', 'shutdown', 
    #    service.shutdown) 
    
    # AT this point we start the reactor and engage the application. Everything 
    # from this point on is asnychronous and handled via the reactors callback
    # system.     
    reactor.run()
    
def sigint_handler(signal, frame):
    global service
    # TODO Cool alert message
    LOG.info('System recieved SIGINT - shutting down all connections and services now')
    # shutdown the reactor
    from twisted.internet import reactor
    # TODO shutdown the reactor AFTER the shutdown event processes
    reactor.callFromThread(service.shutdown)
    
def sighup_handler(signal, frame):
    global service
    # TODO Cool alert message
    LOG.info('[%d] System recieved SIGHUP [%s]' % (os.getpid(), signal))
    # shutdown the reactor
    from twisted.internet import reactor
    # TODO shutdown the reactor AFTER the shutdown event processes
    reactor.callFromThread(service.rehash)

# Setup the signal handlers that the servers need to be aware of as the
# application daemon processes
signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGHUP, sighup_handler)    
    
# Here we begin setting up the application initialization routines almost like a 
# main method but we don't officially have one. All components passed this area 
# are used exclusively in the setup and configuration of the Thor application
from twisted.application import service
application = service.Application('Thor')

# Execute the application. All application initialization logic has been cleared, 
# arguments parsed, and application initialized. From here on out we're in the
# hands of Thor mission control.
execute(application, args, options)

# End of application execution. The main thread will exit after the reactor dies
# in the execute method we will fall through to this point
LOG.debug('Apllication execution completed')