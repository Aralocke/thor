from zope.interface import implements, Interface, Attribute

class ITriggerable(Interface):
    """
    Not implemented
    """

class IStagedTriggerable(Interface):

	def addEventTrigger(phase, eventType, function, *args, **kwargs):
		"""
		"""

	def fireEventTrigger(trigger):
		"""
		"""

	def removeEventTrigger(trigger):
		"""
		"""