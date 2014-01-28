from twisted.internet import reactor, task
from thor.app.crawler import metrics

class NoParentException(Exception):
	pass

class Task(task.LoopingCall):

	__callback = None
	parent = None

	def __init__(self, target,  length, interval):

		task.LoopingCall.__init__(self, self.execute)

		self.target = target
		self.interval = interval

		self.length = length

		self.requests = 0

	def completed(self, passThrough=None):

		print passThrough

		time = (self.clock.seconds() - self.starttime)

		print 'Task for target [%s] completed after %d requests. Task took %s seconds to complete' % (
			self.target, self.requests, time)

	@metrics.metric('execute_task')
	def execute(self):
		try:
			# Houston, we have a problem
			if self.parent is None:
				raise NoParentException('Parent has not bee set on a task')
			# This must be a thread safe operation becuase there are no locks within 
			# the primary crawler application. by using the reactor's main thread to 
			# initialize the requests everything stays thread safe and asynchronous
			reactor.callFromThread(self.parent.executeTask, self)
		finally:
			# This will handle our shutdown and time detection routines
			if self.isActive():
				self.stop()

	def failed(self, failure=None):
		if failure is not None:
			# If the failure result has the HTTP response code we wnat to log that
			# data here otherwise pass on the failure to the next object in the chain
			if hasattr(failure, 'code'):
				print 'Task failed on call to [%s] -> Response code %s' % (self.target, 
					failure.code)
				return failure
		# This case will probably NEVER be used but need to have it either way. But we 
		# keep it as a backup in case the failure doesn't supply HTTP error
		print 'Task failed on call to [%s]' % self.target
		return failure

	def getTimeElapsed(self):
		return (self.clock.seconds() - self.starttime)

	def getTimeRemaining(self):
		return ((self.length + self.starttime) - self.clock.seconds())

	def isActive(self):
		return (self.clock.seconds() - self.starttime) > self.length

	def report(self, passThrough=None):
		return passThrough

	def setCrawler(self, crawler):
		self.parent = crawler

	def start(self, now=False):

		self.__callback = task.LoopingCall.start(self, self.interval, now)
		self.__callback.addBoth(self.completed)
