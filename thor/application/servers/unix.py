from thor.application import server

class UNIXServer(server.Server):
    def __init__(self, socket=None):
        server.Server.__init__(self, asgard=None)