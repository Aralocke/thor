from thor.common.core import event

class Hooked(object):

	def __init__(self):
		self.__hooks = {}

	def addHook(self, eventType, function, *args, **kwargs):
		# Assertion to make sure that our callable function is actually
		# a valid callable function
		assert callable(function), "%s is not callable" % function
		# If the eventType doesn't exist yet we are going to create a new
		# event listener and attach it at the index in the list
		if eventType not in self.__hooks:
			self.__hooks[eventType] = event.EventListener(eventType)
		# The trigger ID returned is going to be the UID of the event that was
		# created. This can be used to remove the trigger to the event
		triggerID = self.__hooks[eventType].addTrigger(function, *args, **kwargs)
		# We return a tuple containing the type of hook we're adding as well as the
		# trigger ID to the hook
		return (eventType, triggerID)

	def fire(self, eventType, consumeErrors=True):
		print 'FIRING EVENT [%s]' % (eventType)
		trigger = self.__hooks.get(eventType)
		# We retrieve a list of the available hooks by key. If none exist we're goinng
		# to ignor ethe rest of the call sequence and go back to processing
		if trigger is not None:
			return trigger.fireEvent()
		# Might be useful down the road to know when we're calling a hook that 
		# doesn't exist or hasn't been associated yet ...
		if not consumeErrors:
			raise Exception('No listener available for hook: %s' % eventType)

	def unhook(self, eventType, triggerID=None, consumeErrors=True):
		hook = self._eventTriggers.get(eventType)
		# Retrieve the event with the given type. If none exist we'll get out
		# here and move forward without processing
		if hook is not None:
			return hook.removeTrigger(triggerID)
		# Might be useful down the road to know when we're removing a hook that 
		# doesn't exist ...
		if not consumeErrors:
			raise Exception('No listener available for hook: %s' % eventType)