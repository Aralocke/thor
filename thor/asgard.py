from thor.common import service

__SERVICE_STATION__ = 'master'
__SERVICE_NODE__    = 'node'
__SERVICE_SLAVE__   = 'slave'

class Asgard(service.Service):
    
    __REALM_NAME = 'Asgard'
    
    def __init__(self, config, name = None, type = __SERVICE_SLAVE__):
        # Call the parent class which will setup all off the thread
        # controls which we'll use later
        service.Service.__init__(self, config)
        
        # We automatically insitalize ourselves NOT as a master
        # but assume we will automatically be a slave process that
        # connects to a master server
        self.type = type
        
        print 'Asgard'
    
    def __str__(self):
        return '[REALM type=%s master=%s]' % (Asgard.__REALM_NAME, self.master)  
    
    # Push an update to the master 
    # As a slave we only care about this in to alert the other crawlers
    # when a new link is found
    def push(self):
        pass
    
    # Pull an update from the master server
    # As a slave we only care about this as far as rertieving data from 
    # the master
    def pull(self):
        pass