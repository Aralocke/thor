import time
from threading import Thread

from thor.common import identity

class Service(identity.Identity):  
    
    def __init__(self, config = None, name = None):
        # Simple call to setup the parent contructor which will 
        # give this class it's uid
        identity.Identity.__init__(self)
        # Print out an initialized message
        self.config = config
        
        self.name = name
        
        self.running = True
        
    def execute(self):
        print 'Service execution'
        # We need to wrap the service within a thread 
        n_thread = Thread(target=self.run)
        n_thread.start()
        
    def handle_stop(self):
        print 'Service exceution stopped'
    
    def handle_exception(self, exception):
        print 'Service Exception: %s' % (exception)
    
    def handle_start(self):
        print 'Service exceution started'    
    
    def run(self, **kwargs):       
        try:
            self.handle_start()
            
            while self.running is True:            
                time.sleep(10)
                
        except Exception as e:            
            self.handle_exception(e)
        finally:    
            self.handle_stop()

# Everything below this point is completely for managing threads of services
__threads = {}
