import os
import signal
import sys

absolute_path = os.path.abspath(__file__)
possible_topdir = os.path.normpath(os.path.join(absolute_path, os.pardir, os.pardir))

if os.path.exists(os.path.join(possible_topdir, 'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from thor import config
from thor import service
from thor.common import environment

def execute(*servers):
    # Signal handler to handle the interrupt event
    signal.signal(signal.SIGINT, sigint_handler)
    
    for server in servers:
        server.start()
        
    for server in servers:
        server.wait()

# Initialization method to setup the asgard class
def make_service(config, name, host = '127.0.0.1', port = 21189, type = None):
    # Initialize the Asgard application service
    app = service.Asgard(config, name=name, type=type)
    # Pass the Asgard application to a server which handles the socket i/o 
    # between the processes
    server = environment.Server(app, host, port) 
    # Return the completed server object
    return server

def sigint_handler(signal, frame):
    # When we recieve the interrupt signal, exit out and
    # get outta dodge
    sys.exit(0)

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