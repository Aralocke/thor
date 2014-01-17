import os, sys

from zope.interface import implements
from twisted.application import service
from twisted.application.service import IServiceMaker
from twisted.internet import reactor
from twisted.plugin import IPlugin
from twisted.python import log, usage

from thor import app
from thor.common.core.service import RUN_OPT_ASGARD, RUN_OPT_CRAWLER, RUN_OPT_WEB

class Options(usage.Options):
	optParameters = [
		# Default controls. This will launch one web server configuration listening on the
		# single ip/port combination. These settings are overriden if either transport specfic 
		# configuartions below are used
		['iface', 'i', '127.0.0.1', '', str],
		['port', 'p', 21189, '', int],
		# Configuration for the HTTPS transport method for the web server. This will override
		# the defaults that get setup above
		['ssl-iface', 'j', None, '', str],
		['ssl-port', 'l', None, '', int],
		# Control the number of processes and threads that get spawned by Asgard
		# and its children applications
		['processes', 'P', 4, 'Number of processes for Asgard to spawn', int],
		['threads', 'T', 8, 'Number of threads for a crawler to spawn', int],
		# Misc command line parameters for handling operational controls and
		# file system locations
		['runmode', 'R', 1, 'Runmode for the application. Usually set by the application', int],
		['socket', 'S', 'data/thor.sock', 'File System location for unix domain socket', str],
	]

	optFlags = [
		['debug', 'b', 'Run the server in debug mode']
	]

	def postOptions(self):
		if self['runmode'] not in (1, 2, 3):
			raise usage.UsageError('')

class ThorServiceMaker(object):

	implements(IServiceMaker, IPlugin)

	tapname = 'thor'
	description = 'Web Application load testing and monitoring tool'
	options = Options

	twistd = []

	def initialize(self, options):
		# check for the existence of the data directory
		if not os.path.exists('data'):
			os.mkdir('data')
		# Before we can really do any configuration for other services, we need to know the
		# options that were used to start twistd. This comes in handy later because we need
		# to pass those options to twistd when we spawn child processes for crawlers
		if self.tapname not in sys.argv:
			raise Exception('Houston we have a problem. Cannot parse argv for tapname')
		# We need to tag on extra options here. Particularly because we are running child
		# processes we do not want to save our state (PID file, etc)
		self.twistd.extend([ 'run.py', '--no_save', '--no-daemon', '--pidfile' ])
		self.twistd.extend([ '--logfile', '/dev/null' ])


	def makeService(self, options): 
		# The twisted application framework provides us with a parent class that we can use
		# to access their framework API. We wrap our application within it
		self.application = service.Application('thor')
		# We're initializing the application before instantiating it. This allows us to setup
		# the file system and other directories that are needed or in use by the application.
		# Particularly the data directory which holds the PID file and primary log directory
		self.initialize(options)
		# Convert the options dictionary into keyword args that we can pass to our application 
		# controllers. FOr some reason, nobody had the smart idea to make usage.Options iterable
		# as a dictionary ... 
		kwargs = {}
		for id, option in options.items(): 
			kwargs[id] = option
		# The first runmode creates a complete master server running the entire stack including
		# a built in web server for handling the web UI components
		if options['runmode'] == RUN_OPT_ASGARD:
			application = app.Asgard( twistdOpts=self.twistd, **kwargs )
		# The second runmode is for launching Crawler processes that manage the workload
		# like worker bees. by themselves they are their own reactor and application
		# but react in different ways than a master application
		elif options['runmode'] == RUN_OPT_CRAWLER:
			application = app.Crawler( **kwargs )
		# The third runmode is to run a Web Server only and none of the worker components. This
		# would connect to a master server and act as a control panel for the nodes
		elif options['runmode'] == RUN_OPT_WEB:
			application = app.Asgard( webServerOnly=True, **kwargs )
		# Set the service parent of our application to be Thor
		# This will allow us to build out and use the API's provided by the built-in twistd 
		# application framework
		application.setServiceParent(self.application)
				
		# The value returned from here needs to be a service or an implementation to the
		# twisted Service
		return application

serviceMaker = ThorServiceMaker()