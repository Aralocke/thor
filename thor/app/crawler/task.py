from twisted.internet import reactor, task

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

		time = (self.clock.seconds() - self.starttime)

		print 'Task for target [%s] completed after %d requests. Task took %s seconds to complete' % (
			self.target, self.requests, time)

	def execute(self):

		if self.parent is not None:
			try:
				reactor.callFromThread(self.parent.executeTask, self)
			except:
				pass

		if (self.clock.seconds() - self.starttime) > (self.length * 60):
			self.stop()

	def failed(self, failure=None):
		print 'Task failed on call to [%s]' % self.target

	def report(self, passThrough=None):
		print 'Task completed call to [%s]' % self.target

	def setCrawler(self, crawler):
		self.parent = crawler

	def start(self, now=False):

		self.__callback = task.LoopingCall.start(self, self.interval, now)
		self.__callback.addCallback(self.completed)
