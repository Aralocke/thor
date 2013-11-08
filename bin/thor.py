import os
import sys

absolute_path = os.path.abspath(__file__)
possible_topdir = os.path.normpath(os.path.join(absolute_path, os.pardir, os.pardir))

if os.path.exists(os.path.join(possible_topdir, 'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from thor import config
from thor import service
from thor.common import environment

def execute(*servers):
    
    # Fire off the startup events for the specific server
    for server in servers:
        server.handle_start()
    
    # Now we are going to tell the apps to load the servers into their own 
    # systhread and then execute the server's async loop
    for server in servers:
        app = server.application
        app.execute()
        
    print 'Service initiated (PID=%s)' % (os.getpid())        
    
# Initialization method to setup the asgard class
def make_service(config, name, host = '127.0.0.1', port = 21189, type = None):
    # Initialize the Asgard application service
    app = service.Asgard(config, name=name, type=type)
    # Pass the Asgard application to a server which handles the socket i/o 
    # between the processes
    server = environment.Server(app, host=host, port=port) 
    # Return the completed server object
    return server

if __name__ == '__main__':
    config.main()
    
    # Containers for the services
    servers = []
    
    # For now we don't have a configuration or a argsparse
    # but we still pass on object for nostalgia
    config = None
    servers.append(make_service(config, 'admin'))
    
    # Execute the servers. From this point on the application
    # is now live (and running)
    execute(*servers)    