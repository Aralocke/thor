import logging

from thor.application import service

class Server(service.BaseService):

    _shutdownHook = None
    
    def __init__(self):
        # initialize the base service and the parent classes
        service.BaseService.__init__(self)
        self.logger = logging.getLogger('thor.application.Server')