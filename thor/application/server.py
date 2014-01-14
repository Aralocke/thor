import logging

from thor.application import service

class Server(service.Service):
    def __init__(self):
        # initialize the base service and the parent classes
        service.Service.__init__(self)
        self.logger = logging.getLogger('thor.application.Server')