import asyncore
import socket

from thor.common import identity
#from thor.common import environment

class Server(identity.Identity, asyncore.dispatcher):
    
    def __init__(self, application, host = None, port = None, threads = 1,
            handler = None):
                
        identity.Identity.__init__(self)
                
        self.application = application
        self.application.set_server(self)
        
        if (handler is not None):
            self.handlerClass = handler
        
        asyncore.dispatcher.__init__(self)
        
        self.running = True
        
        self.host = host or '0.0.0.0'
        self.port = port or '21189'
        
        self.handles = {}
        self.socket_info = {
            'family' : socket.AF_INET,
            'queue'  : 5,
            'type'   : socket.SOCK_STREAM
        }
        
        self.create_socket(self.socket_info['family'], self.socket_info['type'])
        self.set_reuse_addr()
        
        self.bind((self.host, self.port))
        self.address = self.socket.getsockname()
        
        print 'binding to %s:%s' % (self.address[0], self.address[1])
        
        self.listen(self.socket_info['queue'])
        
    def authenticate(self, conn_sock, client_address):
        return True
        
    def handle_accept(self):
        try:
            # Called when a client connects to our socket
            (conn_sock, client_address) = self.accept()
            print 'handle_accept() -> %s' % (client_address[0])
            
            if self.authenticate(conn_sock, client_address):
                print 'conn_made: client_address=%s:%s' % (client_address[0], 
                    client_address[1])
                #client = environment.Client(conn_sock, client_address, self)
            
        except Exception as e:
            print '[EXCEPTION] %s' % (e)
        finally:
            pass
    
    def handle_connect(self):
        print 'handle_connect()' 
        
    def handle_close(self):
        print 'handle_close()'
        self.close()
            
    def handle_start(self):
        pass
        
    def handle_stop(self):
        print 'Server exceution stopped'
    
    def handle_exception(self, exception):
        print 'Server Exception: %s' % (exception)
    
    def handle_start(self):
        print 'Server exceution started'    
    
    def run(self, **kwargs):       
        try:
            self.handle_start()
            
            while self.running is True:            
                asyncore.loop()
                
        except Exception as e:            
            self.handle_exception(e)
        finally:    
            self.handle_stop()