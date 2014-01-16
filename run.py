import os
import logging
import signal
import sys

from thor import application

# Setup the extended paths for the applications and includ ethe sources
# directory within our application namespace
absolute_path = os.path.abspath(__file__)
possible_topdir = os.path.normpath(os.path.join(absolute_path, os.pardir))

# Add the application path if it exists on to the main system path
if os.path.exists(os.path.join(possible_topdir, 'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

def execute(argv, options):
    args = [ sys.argv[0] ]
    if argv is not None:
        args.extend(argv)
    args.append('thor')
    if options is not None:
        args.extend(options)
    sys.argv = args 

    # Debugging purposes only to track the final argument list passed to the
    # twistd application
    #
    # TODO Debug log message of application arguments
    from twisted.scripts.twistd import run

    run() 
    # End of application execution. The main thread will exit after the reactor dies
    # in the execute method we will fall through to this point
    #
    # TODO Log message - Application completed
    sys.exit(1)  

# Determine reactor type. Most *UNIX systems will use a poll based reactor
# while older systems will still user the select type
if os.name == 'nt':
    DEFAULT_REACTOR = 'select'  
else:
    DEFAULT_REACTOR = 'poll'

# Setup the command line option parser
from optparse import OptionParser
parser = OptionParser()

# Separation between the twistd arguments and those that are being passed to our applictaion
# at run time. the twistd args setup the twistd daemon while opt's are passed directly to the
# serviceMaker in our twistd plugin
twistd, opts = [], []

# Not daemonizing the process allows us to actively print to the console. This is really
# only useful for debugging purposes and should never be used to production
parser.add_option('-n', '--no-daemon', 
    help='Do not run in the background', 
    action='store_false', dest='daemonise', default=True)

# The only universally default options that will be used for any incarnation
# of the application. The reactor selector and debug mode are all cross version 
# and the different incarnations all use them
parser.add_option('-b', '--debug', 
    help='Run in the Python Debugger', 
    action='store_true', dest='debug', default=False)
parser.add_option('-r', '--reactor', 
    help='Which reactor to use (see --help-reactors for a list)', 
    dest='reactor', default=DEFAULT_REACTOR)

# The following options are for the locations of the log files and the master server's
# PID file. The master server is the primary monitor and is an incarnation of the
# Asgard application class.
#
# By default both the log file and pid file exist within a directory called 'data' in the
# root directory of the application.
parser.add_option('-l', '--logfile', 
    help='Path to twisted log file.', 
    dest='logfile', default='data/thor.log')
parser.add_option('-P', '--pidfile', 
    help='Path to store PID file', 
    dest='pidfile', default='data/thor.pid')

# The args from 1- are all of the program arguments. The first arg (0th) is the
# program executable and thus useless to us in parsing
sargs = sys.argv[1:]
(options, args) = parser.parse_args(args=sargs)

# initialize the default reactor
reactor = options.reactor + 'reactor'
if options.reactor != DEFAULT_REACTOR:     
    getattr(__import__("twisted.internet", fromlist=[reactor]), reactor).install() 

# Next we run two loops to split the program args with what needs to go to the twistd 
# daemon and what we need sent to our actual application.
#
# The first loop grabs twistd args that we have expected
for option in ('logfile', 'pidfile'):
    if hasattr(options, option):
        twistd.extend(['--'+option, getattr(options, option)])
# The second loop will grab the application arguments and place them into a second list
for option in (''):
    if hasattr(options, option):
        opts.extend(['--'+option, getattr(options, option)])

if not options.daemonise:
    twistd.append('-n')

if options.debug:
    opts.append('-b') 

# Execute the application. All application initialization logic has been cleared, 
# arguments parsed, and application initialized. From here on out we're in the
# hands of Thor mission control.
execute(twistd, opts)

# EOF :: ./run.py