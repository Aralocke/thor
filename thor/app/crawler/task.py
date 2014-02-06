from twisted.internet import task, reactor
from thor.app.crawler import metrics, spider
from thor.common import thread
from thor.common.core import component

class NoParentException(Exception):
	pass

class Task(component.Component):

	parent = None

	def __init__(self, target,  length, interval, rpm=200, startNow=True):
		component.Component.__init__(self)

		self.target = target
		self.interval = interval
		self.clock = reactor
		self.length = length

		if type(startNow) == 'int':
			self.starttime = self.clock.seconds() + int(startNow)
		else:
			self.starttime = 0

		self.rpm = rpm
		self.requests = 0

		#self.semaphore = thread.AvailabilitySemaphore(value=self.rpm)
		self.semaphore = thread.TimeReleaseSemaphore(60, reactor, value=self.rpm)

	def complete(self):
		print 'Completing task'
		self.setState('STOPPED')

	def completed(self, passThrough=None):

		print passThrough

		time = (self.clock.seconds() - self.starttime)

		print 'Task for target [%s] completed after %d requests. Task took %s seconds to complete' % (
			self.target, self.requests, time)

	def createSpider(self):
		# We create the spider and set its target to the task's target
		s = spider.Spider(target=self.target)
		# Save a reference to our task
		s.setTask(self)

		return s

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
		if self.getState('RUNNING'):
			print 'remaining=%d' % self.getTimeRemaining()
			if self.getTimeRemaining() > 0:
				return True
		return False

	def readyToStart(self):
		# The task should remain in the 'new' state until the reactor's scheduler starts 
		# it during its main loop
		if self.getState('NEW'):
			# Allows us to schedule start times based on when they are tasked to begin
			# we only proceed to start the test AFTER the start time has been passed
			#
			# assuming no staggered start options, starttime will actually be the value
			# zero and not a timestamp
			if self.clock.seconds() >= self.starttime:
				return True
		# If we're already called start this function is meaningless
		return False

	def start(self):
		# CHange the state of the task
		self.setState('STARTING')
		# Setup the instance variables we need to track time
		self.starttime = self.clock.seconds()
		# Setup the runtime monitors
		self.requests = 0
		self.runtime = []		
		# Finally we set the task to its active state
		self.setState('RUNNING')

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
		# Number of tasks reaped in an interval threshold
		self.reaped = 0

	def execute(self):
		# We can shut ourselves down, or at least PAUSE ourselves when we have no tasks 
		# running. We automatically return here to avoid any unnecesary process time
		if len(self.tasks) == 0:
			return

		__start = self.clock.seconds()
		# We have no tasks so do not proceed any further
		print 'Executing'
		# ====
		# Inside here is the execution logic for the scheduler algorithm
		# ====
		# If we have tasks we proceed, otherwise we get out and come back in one second
		if self.tasks: 
			# ====
			# start scheduler logic block
			# ====
			self.completed_tasks = []
			# Loop through the existing tasks
			for task in self.tasks:
				# Loop through each listed tasks running a few checks on them before
				# we attempt to queue them out.
				#
				# If the task need sto be started we start it here
				if task.readyToStart():
					task.start()
					# Start the availability semaphore
					task.semaphore.start()
				# Now we check if the task is still active
				if task.isActive():
					# ====
					# The bulk of the scheduling logic happens here. We want to know if
					# we have available requests and if we do, we need to queue them up 
					# within the threadpool
					# ====
					# We calculate how many requests per second by dividing the value 
					# of requests per minute by 60. The value returned is a float
					requests_per_second = float(task.rpm) / 60
					
					# Our minimum is to allow ONE request per iteration. SO the lowest
					# RPM we can do is 60. This is to make entering the loop worth
					# the time expended to get to this logical point
					if int(requests_per_second) < 1:
						requests_per_second = 1

					# After we have our requests per second, we'll loop until we get a
					# new connection count equal to our RPS
					for count in range(int(requests_per_second)):
						# We do NOT want to block. This might be limited to CPython so I can
						# imagine a bug turning up in this location eventually. Adding a 
						# call with blocking=False 'should' return false immediately given the
						# program's inability to acquire a semaphore lock
						if task.semaphore.available():
							# Acquire a semaphore lock
							task.semaphore.acquire()
							# The call to create the spider will chain its returned callback
							# to the release of its internal semaphore. Once we pass off 
							# to the reactor it is all handled asynchronously
							s = task.createSpider()
							# Pass off the spiders execute method to the reactors internal
							# threapool and wait for execution
							reactor.callInThread(s.execute)	
					print '[%s] RPS=%s Semaphores=%d' % (task.target, requests_per_second,
						task.semaphore.getAvailable())
				else:
					task.setState('STOPPING')
					print 'Task [%s] has completed' % task.target
					# Add the task to the list that we will cleanup after we 
					# finish executing
					self.completed_tasks.append(task)
			# Now we run through and complete any tasks and remove them from our task
			# list for the next iteration
			if self.completed_tasks:
				# Cleanup and expiration of the completed tasks
				print 'Pruning %d completed tasks' % len(self.completed_tasks)
				for task in self.completed_tasks:
					# Remove the task from our tracker so that we don't accidentally
					# process it again. After this point we longer care what happens to
					# the task in terms of teh actual application
					self.tasks.remove(task)
					# Calling complete will set the state to shutdown and fire off any 
					# remaining shutdown hooks
					task.complete()
				# Clean up the list and rest it
				self.reaped += len(self.completed_tasks)
				self.completed_tasks = []
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
			print '\tReaped tasks: %d' % self.reaped
			# Reset the runtime container
			runtime, self.runtime = self.runtime, []
			reaped, self.reaped = self.reaped, 0

	def schedule(self, task):
		self.tasks.append(task)

	def stop(self):
		# We need to execute a shutdown of all tasks and requests currently pooled within
		# the scheduler
		#
		# Shutdown the looping call first. We will automatically fire the deferred callback
		# of the looping call so any callbacks will be triggered here
		task.LoopingCall.stop(self)

	def start(self, threads=8):		
		# Grab the threadpool instance and override some settings with what we need
		threadpool = reactor.getThreadPool()
		# We set the internal reactor's thread pool to be the number of spiders we wnat
		# to run
		threadpool.adjustPoolsize(maxthreads=threads)
		# Start the internal looping call immeadietly and begin processign requests
		self.__callback = task.LoopingCall.start(self, 1.0, now=True)

	def setCrawler(self, crawler):
		self.parent = crawler