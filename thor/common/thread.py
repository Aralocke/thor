from threading import Condition, Lock

class AvailabilitySemaphore(object):

	def __init__(self, value=1):
		# We wrap the logic here within a synchronization condition
		self.__condition = Condition(lock=Lock())
		# The value of the bound we will allocate
		self.__value = value

	def acquire(self):
		self.__condition.acquire()
		# We will be unable to acquire any locks if we are currently full 
		# on holds. We will just return False here
		try:
			if self.__value == 0:
				return False
				
			self.__value = (self.__value - 1)
		# Release the hold on the mutex and return a value of True because 
		# we CAN allocate a value
		finally:
			self.__condition.release()
		
		return True

	def available(self):
		# Identical in logic to acquire however we don't modify the value
		self.__condition.acquire()
		try:
			if self.__value == 0:
				return False
		finally:
			self.__condition.release()
		
		return True

	def getAvailable(self):
		self.__condition.acquire()
		try:
			return self.__value
		finally:
			self.__condition.release()

	def release(self):
		self.__condition.acquire()
		try:
			self.__value = self.__value + 1	
		finally:
			self.__condition.release()