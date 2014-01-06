from thor.application.servers import tcp

class WebServer(tcp.TCPServer):
    def __init__(self, asgard=None, iface='0.0.0.0', port='21189', 
    	root=None):
        tcp.TCPServer.__init__(self, asgard=None)