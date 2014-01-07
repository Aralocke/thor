from thor.application import server

class TCPServer(server.Server):
    def __init__(self, asgard=None, iface='0.0.0.0', port='21189'):
        server.Server.__init__(self, asgard=asgard)