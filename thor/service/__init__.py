# List of all the classes that are automatically loaded by this package
__all__ = ['Asgard']

Asgard = None

# Import the server when the enviornment is setup
from thor import asgard

# Set the reference so that we can include it later on
Asgard = asgard.Asgard

# Later on we will build the environment in here and have settings
# etc
#
# TODO build environment for TCP connections between nodes