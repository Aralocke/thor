from thor.common.core import service

class Asgard(service.DaemonService):

	def __init__(self, **kwargs):
		service.DaemonService.__init__(self)