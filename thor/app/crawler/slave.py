from twisted.internet import reactor
from twisted.application import service
from twisted.python import usage

from thor.app.realm import protocol
from thor.app.crawler import metrics
from thor.app.crawler import task as schedule
from thor.app.crawler import spider as crawler
from thor.app.crawler.task import NoParentException
from thor.common.core.connections import unix  
# Stupid naming conventions on my part .. maybe
from thor.common.core.service import DaemonService
from thor.common.core.service import RUN_OPT_CRAWLER


class Options(usage.Options):
	optParameters = [
		# Control the number of threads that get spawned
		['threads', 'T', 8, 'Number of threads for a crawler to spawn', int],
		# Misc command line parameters for handling operational controls and
		# file system locations
		['runmode', 'R', 1, 'Runmode for the application. Usually set by the application', int],
		['socket', 'S', 'data/thor.sock', 'File System location for unix domain socket', str],
	]

	optFlags = [
		['debug', 'b', 'Run the server in debug mode']
	]

class Crawler(DaemonService):

	def __init__(self, socket=None, **kwargs):
		# Run the init routines on the parent class
		# this sets up all of the Twisted logic needed
		# later on
		DaemonService.__init__(self, **kwargs)
		DaemonService.setName(self, 'Crawler')
		self.threads = kwargs.get('threads', 8)
		# The socket we need to connect to holds our connection to the primary
		# Asgard process running on this machine
		self.socket = socket
		# List of spiders that we run to do crawling operations
		self.spiders = {}
		# We maintain a link to the primary Asgard socket 
		self.connection = None
		# Referenc to the scheduler that controls the requests per minute going out
		self.scheduler = schedule.Scheduler()
		self.scheduler.setCrawler(self)
		self.scheduler.threshold = kwargs.get('threshold',)

	@metrics.metric('addTarget')
	def addTarget(self, target, **kwargs):
		target = target

		rpm = int(kwargs.get('rpm', 60))

		if rpm < 60: rpm = 60

		# Length is in muniutes
		length = int(kwargs.get('length', 1)) * 60

		# Interval is ALWAYS in seconds
		interval = float(kwargs.get('interval', 1))

		startNow = kwargs.get('startNow', True)

		task = schedule.Task(target, length, interval, rpm=rpm, 
			startNow=startNow)
		task.setCrawler(self)

		print ('Adding new target [%s] at a %s second interval with %d requests per minute'
		      ' (test will last %d minutes)' % (target, interval, rpm, int(length / 60)))

		self.scheduler.schedule(task)

	def create_connection(self, path=None):
		# We need to be given a path to the UNIX socket we are connecting to
		# the default should be placed in 'data/thor.sock'
		socket = path or 'data/thor.sock'
		# After we have the path we initialize a unix connection on the socket
		connection = unix.UNIXConnection(path=socket, 
			# A single event driven communication protocol for all clients to use
			# this handles all of the transformations of text and messages between
			# the servers and respective clients
			protocol=protocol.ClientProtocol) 
		connection.setName('Crawler_UNIXConnection')
		# After we create the connection we need to set ourselves as the parent
		connection.setServiceParent(self)
		# By setting the connection service to be part of our multi service it is
		# automatically started by the twisted system running in the background
		# what we return is just the started connection and "should" be ready to go
		return connection

	def startup(self):
		# We need to establish our connection to the primary asgard server and initialize
		# the main socket routines
		self.connection = self.create_connection(path=self.socket)
		# Once we establish our connection to the Asgard process, we are goign to initiate
		# the calls to spawn our spiders. Each Spider represents 1 distinct functional crawler
		# of the http target
		for i in range(self.threads):
			spider = self.create_spider()
		# setup the scheduler 
		self.scheduler.start(self.threads)

		# Internal targeting
		kwargs = {'target': 'http://pathways.sait.internal/login', 'interval': 0, 'length': 1}
		reactor.callLater(5, self.addTarget, **kwargs)

def launcher(options):
	socket = None
	# The config object is defined above with the parameters that we expect. These options
	# are passed during the creation of the process within asgard
	config = Options()
	# We try to parse the configuration objects. If we have toruble we are going to attempt
	# to spawn with defaulted parameters. The core fo which is the socket options and thread
	# count.
	try:
		config.parseOptions()
	except usage.UsageError, errortext:
		# The config object actually is a dictionary of values that have been parsed and can 
		# be treated like any actual dictionary
		config = {
			'runmode' : RUN_OPT_CRAWLER,
			'threads' : 4
		}
		# The socket value MUST be present, therefore we include it as a separate variable and
		# not as part of teh above dictionary
		socket = 'data/thor.sock'

	if socket is not None:
		socket = config['socket']
	del config['socket']

	# The twisted application framework provides us with a parent class that we can use
	# to access their framework API. We wrap our application within it
	parent = service.Application('thor')	
	
	# Parse the options we get into a keywork argument list. This list is passed to the Crawler
	# process on initialization. These arguments are set by ther master Asgard process when
	# spawning children
	kwargs = {}
	for id, option in config.items(): 
		kwargs[id] = option
	# The application is created here when we build the primary daemonservice that controls
	# the physical process
	application = Crawler(socket, **kwargs)

	# Set the service parent of our application to be Thor
	# This will allow us to build out and use the API's provided by the built-in twistd 
	# application framework
	application.setServiceParent(parent)

	# The extra step we have to take here is to start the service ourselves. This one time
	# operation only has to happen because we are initiating things and not the reactor, or 
	# the twistd daemon. setServiceParent will only chain a startService call when a service
	# is already running
	application.startService()

	# The value returned from here needs to be a service or an implementation to the
	# twisted Service
	return application