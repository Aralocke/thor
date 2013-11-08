import socket
import asyncore

from thor.common import identity

class Client(identity.Identity, asyncore.dispatcher):
    
    def __init__(self, conn_sock, client_address, server, buffer_len = 1024):
        self.server             = server
        self.client_address     = client_address
        self.buffer             = ""
        self.buffer_len         = buffer_len
 
        # We dont have anything to write, to start with
        self.is_writable        = False
        self.is_readable        = True
 
        # Create ourselves, but with an already provided socket
        asyncore.dispatcher.__init__(self, conn_sock)
        print 'created handler; waiting for loop'
        
    def readable(self):
        return self.is_readable
    
    def writable(self):
        return self.is_writable
    
    def handle_read(self):
        print 'handle_read'
        data = self.recv(self.buffer_len)
        print 'after recv'
        
        if data:
            print 'got data'
            self.buffer += data
            self.is_writable = True  # sth to send back now
        else:
            print 'got null data'
 
    def handle_write(self):
        print 'handle_write'
        
        if self.buffer:
            sent = self.send(self.buffer)
            print 'sent data'
            self.buffer = self.buffer[sent:]
        else:
            print 'nothing to send'
            
        if len(self.buffer) == 0:
            self.is_writable = False
 
    # Will this ever get called?  Does loop() call
    # handle_close() if we called close, to start with?
    def handle_close(self):
        print 'handle_close -> conn_closed: client_address=%s:%s' % (self.client_address[0],
                      self.client_address[1])
        self.close()