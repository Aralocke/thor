from thor.common.core import service
import treq

class Spider(service.Service):

	def __init__(self):
		# We need to initialize this spider service object
		service.Service.__init__(self)

	def completed(self, data=None):
		return data

	def execute(self, target):
		d = treq.get(target)
		d.addCallback(self.completed)
		return d