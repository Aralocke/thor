import socket
import ssl
import sys

import eventlet
import greenlet

class Server(object):
    
    def __init__(self, application, host = None, port = None, threads = 1):
        self.application = application
        
        self.host = host or '0.0.0.0'
        self.port = port or '21189'
        
        self.pool = eventlet.GreenPool(threads)
        self.greenthread = None
        self.socket_info = {}
    
    def start(self):
        pass
    
    def wait(self):
        pass