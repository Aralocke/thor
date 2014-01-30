from twisted.internet import task, reactor
from thor.app.crawler import metrics

class NoParentException(Exception):
	pass

class Task(object):

	parent = None

	def __init__(self, target,  length, interval):
		self.target = target
		self.interval = interval
		self.clock = reactor
		self.length = length

		self.rpm = 200
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

class Scheduler(task.LoopingCall):

	__callback = None
	parent = None
	threshold = 60

	def __init__(self):
		# We build the scheduler on top of a looping call object. The goal is to trigger
		# every second and keep up a continued requests per minute rate
		task.LoopingCall.__init__(self, self.execute)
		self.tasks = []
		# We track the amount time 1 minute of execution loops take to complete
		self.runtime = []

	def execute(self):
		__start = self.clock.seconds()
		# We have no tasks so do not proceed any further
		print 'Executing'
		# ====
		# Inside here is the execution logic for the scheduler algorithm
		# ====
		# If we have tasks we proceed, otherwise we get out and come back in one second
		if self.tasks: 
			pass
			# ====
			# start scheduler logic block
			# ====
			#from time import sleep
			#sleep(0.5)
			# ====
			# End scheduler logic block
			# ====
		# Save the stop time
		__stop = (self.clock.seconds() - __start)
		# Lets monitor the polling time for the scheduling algorithm
		print 'Spent %s seconds executing scheduler' % (round(__stop, 5))
		# add the stop time to the runtime list
		self.runtime.append(__stop)

		# Run the debuging and profiling of the scheduler 
		if len(self.runtime) == self.threshold:
			
			processing_time = 0
			overflow_time = 0

			for elapsed in self.runtime:
				# Save the amount of elapsed time in a summary value
				processing_time += elapsed
				# next if we spent MORE than 1 second processing we need to know
				# how much longer we spent
				if elapsed > 1: 
					overflow_time += (elapsed - 1)

			# Extra statistics
			free_time = int(self.threshold) - processing_time
			free_percentage = free_time / self.threshold * 100

			# End of loop, print out debug data
			print 'Debug for %d iterations' % (int(self.threshold))
			print '\tProcessing time: %s' % round(processing_time, 5)
			print '\tOverflow time: %s' % round(overflow_time, 5)
			print '\tFree time: %s (%s unused)' % (round(free_time, 5), 
				round(free_percentage, 2))
			# Reset the runtime container
			runtime, self.runtime = self.runtime, []

	def schedule(self, task):
		self.tasks.append(task)

	def stop(self):
		# We need to execute a shutdown of all tasks and requests currently pooled within
		# the scheduler
		#
		# Shutdown the looping call first. We will automatically fire the deferred callback
		# of the looping call so any callbacks will be triggered here
		task.LoopingCall.stop(self)

	def start(self):
		# Start the internal looping call immeadietly and begin processign requests
		self.__callback = task.LoopingCall.start(self, 1.0, now=True)

	def setCrawler(self, crawler):
		self.parent = crawler