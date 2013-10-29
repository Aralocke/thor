# List of all the classes that are automatically loaded by this package
__all__ = ['Server']

# Have we configured the environment yet?
# We only configure once so once this is set to true we have a problem
# if we have to change
_configured = False

Server = None

# Import the server when the enviornment is setup
from thor.common.environment import server

# Set the reference so that we can include it later on
Server = server.Server

# Later on we will build the environment in here and have settings
# etc
#
# TODO build environment for TCP connections between nodes