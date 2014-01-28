from thor.common.core import service
import treq

class Spider(service.Service):

	def __init__(self):
		# We need to initialize this spider service object
		service.Service.__init__(self)

	def completed(self, response):
		return response

	def execute(self, target):
		# The method call to implementation is specific and can be overriden or changed
		# however we ALWAYS attach a deferred callback here
		d = treq.get(target)
		# We attach our own internal callbacks to view / process the data that is returns
		d.addCallbacks(self.completed, self.failure)
		# Return the calls's defered
		return d

	def failure(self, failure):
		return failure

	def implementation(self, target, **kwargs):
		# Whatever implementation is used we MUST return a deferred that fires when the 
		# request has been completed
		d = treq.get(target)
		return d