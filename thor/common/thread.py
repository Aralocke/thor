from threading import Condition, Lock, RLock

class AvailabilitySemaphore(object):

	def __init__(self, value=1):
		# We wrap the logic here within a synchronization condition
		self.condition = Condition(lock=Lock())
		# The value of the bound we will allocate
		self.value = value

	def acquire(self):
		self.condition.acquire()
		# We will be unable to acquire any locks if we are currently full 
		# on holds. We will just return False here
		try:
			if self.value == 0:
				return False

			self.value = (self.value - 1)
		# Release the hold on the mutex and return a value of True because 
		# we CAN allocate a value
		finally:
			self.condition.release()
		
		return True

	def available(self):
		# Identical in logic to acquire however we don't modify the value
		self.condition.acquire()
		try:
			if self.value == 0:
				return False
		finally:
			self.condition.release()
		
		return True

	def getAvailable(self):
		self.condition.acquire()
		try:
			return self.value
		finally:
			self.condition.release()

	def release(self):
		self.condition.acquire()
		try:
			self.value = self.value + 1	
		finally:
			self.condition.release()

class TimeReleaseSemaphore(AvailabilitySemaphore):

	def __init__(self, interval, clock, value=1):
		AvailabilitySemaphore.__init__(self,value)
		# We need an instance variable to record the start time and intervals
		self.timestamp = 0
		self.interval = interval
		# This is usually the reactor we are using
		self.clock = clock
		# We need to use a re-entrant write lock to override the condition and 
		# the synchronization methods we use
		self.condition = Condition(lock=RLock())
		# The number of released locks that are now waiting for a new interval period
		self.waiting = 0
		self.reset = False

	def acquire(self):
		if self.condition.acquire(blocking=False):
			# We will be unable to acquire any locks if we are currently full 
			# on holds. We will just return False here
			try:
				if self.available():
					self.value = (self.value - 1)

					return True
			# Release the hold on the mutex and return a value of True because 
			# we CAN allocate a value
			finally:
				self.condition.release()

		return False		

	def available(self):
		# Identical in logic to acquire however we don't modify the value
		if self.condition.acquire(blocking=False):
			try:
				# We need to compute the availability within our interval time
				# frame.
				#
				# The goal here is to check if the current time has exceeded our 
				# timestamp for the last reset of the semaphore
				if self.clock.seconds() >= (self.timestamp + self.interval):
					print '\tResetting semaphore'
					self.value = self.value + self.waiting
					self.timestamp = self.clock.seconds()
					self.waiting = 0

				# If we don't have any available locks we can return here	
				if AvailabilitySemaphore.available(self):
					return True
			finally:
				self.condition.release()

		return False

	def release(self):
		self.condition.acquire()
		try:
			self.waiting = self.waiting + 1	
		finally:
			self.condition.release()

	def start(self):
		self.condition.acquire()
		try:
			self.timestamp = self.clock.seconds()	
		finally:
			self.condition.release()