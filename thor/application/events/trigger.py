from twisted.internet import defer
from thor.application.events import event

class Triggers(object):

	def __init__(self):
		self._eventTriggers = {}

	def addEventTrigger(self, phase, eventType, function, *args, **kwargs):
		assert callable(function), "%s is not callable" % function
		if eventType not in self._eventTriggers:
			self._eventTriggers[eventType] = event.ThreePhaseEvent()
		triggerID = self._eventTriggers[eventType].addTrigger(phase, function,
		    *args, **kwargs)
		return (eventType, triggerID)

	def fireEventTrigger(self, eventType):
		print '-> received event :: %s' % (eventType)
		event = self._eventTriggers.get(eventType)
		if event is not None:
			event.fireEvent()

	def removeEventTrigger(self, triggerID):
		pass