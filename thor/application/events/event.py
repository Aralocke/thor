from twisted.internet import defer
from twisted.python import log

class Event(object):
	def __init__(self):
	    self.callables = []

	def addTrigger(self, callable, *args, **kwargs):
		pass

	def fireEvent(self):
	    pass

class StagedEvent(Event):

	def __init__(self, state='INIT'):
		Event.__init__(self)
		self.state = state
		self._states = {}

	#def addTrigger(self, phase, callable, *args, **kwargs): pass

	def addTriggerableState(self, state):
	    if state in self._states:
	    	raise KeyError('State already exists')
	    self._states[state] = []

	def fireEvent(self):
		pass

	def removeTriggerableState(self, state):
	    pass

	def setState(self, state='INIT'):
		self.state = state

class ThreePhaseEvent(StagedEvent):
	def __init__(self):
		StagedEvent.__init__(self, state='BASE')

		self.addTriggerableState('before')	
		self.addTriggerableState('during')	
		self.addTriggerableState('after')

	def addTrigger(self, phase, callable, *args, **kwargs):
		if phase not in ('before', 'during', 'after'):
		    raise KeyError("invalid phase")
		if phase not in self._states:
			raise KeyError('Unknown state/stage')

		self._states[phase].append((callable, args, kwargs))
		return phase, callable, args, kwargs

	def fireEvent(self):
		self.setState('BEFORE')
		self.finishedBefore = []
		beforeResults = []
		while self._states['before']:
			callable, args, kwargs = self._states['before'].pop(0)
			self.finishedBefore.append((callable, args, kwargs))
			try:
			    result = callable(*args, **kwargs)
			except:
			    log.err()
			else:
			    if isinstance(result, defer.Deferred):
			        beforeResults.append(result)
		defer.DeferredList(beforeResults).addCallback(self._continueFiring)


	def _continueFiring(self, ignored):
		self.setState('BASE')
		self.finishedBefore = []
		for phase in self._states['during'], self._states['after']:
			while phase:
			    callable, args, kwargs = phase.pop(0)
			    try:
			        callable(*args, **kwargs)
			    except:
			        log.err()