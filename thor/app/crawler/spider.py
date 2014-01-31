import treq

class Spider(object):

	task = None
	callback = None

	def __init__(self, target):
		self.target = target

	def completed(self, response):
		return response

	def execute(self):
		# The method call to implementation is specific and can be overriden or changed
		# however we ALWAYS attach a deferred callback here
		self.callback = self.implementation()
		# We attach our own internal callbacks to view / process the data that is returns
		self.callback.addCallbacks(self.completed, self.failure)
		# We add a second callback to trigger on a success or failure. This is a hook 
		# point for releasing the semaphore lock that we use
		self.callback.addBoth(self.onResult)

	def failure(self, failure):
		return failure

	def implementation(self):
		# Whatever implementation is used we MUST return a deferred that fires when the 
		# request has been completed
		d = treq.get(self.target)
		return d

	def onResult(self, passThrough=None):
		# This function gives us a single entry point in the callback chain
		# to release the semaphore lock that wa sused to call us
		self.task.semaphore.release()
		# Return the result. This passThrough could be either a result or a failure
		return passThrough

	def setTask(self, task):
		self.task = task