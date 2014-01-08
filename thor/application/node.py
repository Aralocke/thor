import logging
import signal

from twisted.application import internet, service
from twisted.internet import defer
from thor.application import service

class Node(service.BaseService):

	def __init__(self, asgard=None, socket=None):
		service.BaseService.__init__(self, asgard)