from zope.interface import implements, Interface, Attribute

class IHookService(Interface):

	def shutdownHook(callback):
		"""
        Run application specific shutdown code or chain shutdown code
        to the callback chain passed. A service should implment these methods
        to allow extending services to implement shutdown logic.

        This give sthe application designer the opportunity to seperate the logic
        of the twisted services from their actual application.

        This function MUST result in the firing of the callback to finish the shutdown
        process.
		"""

	def startupHook(callback):
		"""
        Run application specific startup code or chain startup code
        to the callback chain passed. A service should implment these methods
        to allow extending services to implement startup logic.

        This give sthe application designer the opportunity to seperate the logic
        of the twisted services from their actual application.

        This function MUST result in the firing of the callback to finish the startup
        process.
		"""