from __future__ import print_function

import os
import sys

from thor.common import config
from thor import exception

# Wrapper file to setup and configure the application.
# This file wraps the thor.common.config.py file and sets up the
# environment to configure the application including the command
# line parser used by the app

#CONF = config.CONF
CONF = None

from argparse import ArgumentParser

# Locate the configuration file in a predefined location or becaus ethe
# command line argument for one has been passed
def find_configuration():
    pass

# Initialize the main routine and setup the configuration service
# By default we parse any command line arguments here before proceeding
def main():
    # Instantiate a configuration object
    config = None 
    
    try:
        pass       
    except Exception as e:
        print('Config Exception: %s' % (e), sys.stderr)
        sys.exit(1)
    
    # We return what we have. For now this will return a null value
    # but afte rthe configuration system is built this should never reach this
    # point without a valid configuration object being returned
    return config