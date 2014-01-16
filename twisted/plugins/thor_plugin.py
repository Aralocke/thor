import os

from zope.interface import implements
from twisted.application import service
from twisted.application.service import IServiceMaker
from twisted.internet import reactor
from twisted.plugin import IPlugin
from twisted.python import usage

from thor import app

class Options(usage.Options):
	optParameters = [
		['runmode', 'R', 1, 'Runmode for the application. Usually set by the application', int],
		['processes', 'P', 4, 'Number of processes for Asgard to spawn', int],
		['threads', 'T', 8, 'Number of threads for a crawler to spawn', int],
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

	def initialize(self, options):
		# check for the existence of the data directory
		if not os.path.exists('data'):
			os.mkdir('data')

	def makeService(self, options):
		# We're initializing the application before instantiating it. This allows us to setup
		# the file system and other directories that are needed or in use by the application.
		# Particularly the data directory which holds the PID file and primary log directory
		self.initialize(options)
		# The first runmode creates a complete master server running the entire stack including
		# a built in web server for handling the web UI components
		if options['runmode'] == 1:
			application = app.Asgard( processes=options['processes'])
		# The second runmode is for launching Crawler processes that manage the workload
		# like worker bees. by themselves they are their own reactor and application
		# but react in different ways than a master application
		elif options['runmode'] == 2:
			application = app.Crawler( threads=options['threads'] )
		# The third runmode is to run a Web Server only and none of the worker components. This
		# would connect to a master server and act as a control panel for the nodes
		elif options['runmode'] == 3:
			application = app.Asgard(webServerOnly=True)
				
		# The value returned from here needs to be a service or an implementation to the
		# twisted Service
		return application

serviceMaker = ThorServiceMaker()