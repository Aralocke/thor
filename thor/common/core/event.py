from twisted.internet import defer
from thor.common.core import object

class Event(object.Object):

	def __init__(self, function, *args, **kwargs):
		object.Object.__init__(self)

		assert callable(function), 'Function [%s] is not callable' % function
		self.callable = function

		self.args = (args, kwargs)

	def fire(self):
		try:
			args, kwargs = self.args
			result = self.callable(*args, **kwargs)
		except Exception as e:
			print e

		return result	

class EventListener(object.Object):

	callback = None

	def __init__(self, eventType):
		object.Object.__init__(self)

		self.__triggers = {}
		self.event = eventType

	def addTrigger(self, function, *args, **kwargs):
		# We create an instance of the triggered event first. This allows for
		# the UID field to be populated and the assertions to check for the
		# callable function we gave it
		trigger = Event(function, *args, **kwargs)
		# We save callable triggers by the triggerID which is a string UID
		self.__triggers[trigger.getUID()] = trigger

	def _eventCallback(self, passThrough=None):
	    pass

	def fireEvent(self, consumeErrors=True):
		# We don't proceed if there are no events to fire
		if self.__triggers:
			# Save a list of the returned results from the calls to the events
			# this list gets sent into a deferred list and will callback after all 
			# have been completed
			results = []
			for uid, trigger in self.__triggers.iteritems():
				try:
					result = trigger.fire()
				except Exception as e:
					print e
				else:
					if isinstance(result, defer.Deferred):
						results.append(result)
					else:
						results.append(defer.succeed(True))
			# If we are given any deferred results we will add them to a deferred
			# list and call our listeners callback when they have completed
			if results:
				return defer.DeferredList(results).addCallback(self._eventCallback)
		# We should only return a completed deferred when we don't have anything to
		# process because the loop will automatically add a succeeded deferred for
		# every trigger regardless of its return value
		return defer.succeed(True)

	def removeTrigger(self, triggerID, consumeErrors=True):
		if triggerID in self.__triggers:
			del self.__triggers[triggerID]
		elif not consumeErrors:
			raise Exception('Trigger id [%s] not found' % triggerID)