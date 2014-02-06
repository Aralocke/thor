# ====
# This test is designed for running the Crawler in a controlled environment
# and watching how the scheduler handles assigning tasks to the internal spider
# threads that it manages.
#
# We maintain a list of targets we want to test. This list is pased to the
# Crawler after we giv eit a fake start
targets = []
# Each target tuple gets appended on to the set
# ['target', rpm, interval, length (in minutes)]
targets.append(['http://pathways.sait.internal/login', 2000, 2, 3])
targets.append(['http://phantomnet.net', 50, 2, 1])
# 
# This test is for purely debugging purposes and will print all dat to the console
# during run time
# ====
import os
import sys

from twisted.application import service
from twisted.internet import reactor

# Debugging purposes to track application start time
START_TIME = reactor.seconds()
# =====
# Path configuration
# Absolute path to the file we're currently running
absolute_path = os.path.abspath(__file__)
# Path to the directory we're in, but going back to levels
parent_path = os.pardir+'/../../'
# Normalized path to the primary application directory
possible_topdir = os.path.normpath(os.path.join(absolute_path, parent_path))
# If the thor package exists, we're going to add an entry on our path to it
# so that the namespaces line up properly
if os.path.exists(os.path.join(possible_topdir, 'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)
# After this point we can include any of the thor packages in this test
# =====
#
# Include the option parser
from thor.app import parser
parser = parser.OptionParser()

# Control the number of spider threads that we spawn inside the threadpool
# by default we will spawn to to watch how the concurrency locks are handled
# by the application
parser.add_option('-t', '--threads', 
    help='Number of threads to run inside the spider pool', 
    dest='threads', type='int', default=2)

parser.add_option('-T', '--threshold', 
    help='Number of scheduled iterations in a set', 
    dest='threshold', type='int', default=60)

# Parse the options and begin seting up the application environment
(options, args) = parser.parse_args(args=sys.argv[1:])

# Sanity check. The minimum number of executors within the thread pool
# can be 2 so we can demonstrate locking
if int(options.threads) < 2:
	options.threads = 2

# Build the keyword arguments that we are going to send to the Crawler 
# application to fake proper initialization
kwargs = {}
for option in ('threads','threshold'):
	if hasattr(options, option):
		kwargs[option] = getattr(options, option)

from thor.app import crawler
# Instantiate the Crawler
#
# Create the Crawler application with a fake socket object. We are not
# setting up the service but rather using procedural method calls to
# build the application
parent = service.Application('thor')
application = crawler.Crawler(socket=None, **kwargs)
application.setServiceParent(parent)
# From here the application is instantiated but we must build it like a 
# traditional Crawler would be built to preserve the funcitonality of the 
# test. 
#
# Startup of the Crawler
print 'Crawler started with %d spiders' % (application.threads)

# After we start the loop, give the scheduler something to munch on, and 
# away we go
for (target, rpm, interval, length) in targets:
	# We need to parse the tuple into a target that the scheduler can use to 
	# start crawling pages
	#
    # Create the keyword argument list we pass to the Crawler application
    kwargs = {'interval': interval, 'length': length, 'rpm': rpm, 
	    'startNow': True}
    # Add the new target to the application
    application.addTarget(target, **kwargs)

# Now we need to start the scheduler loop
print 'Starting the scheduler'
application.scheduler.start(options.threads)

# Activate and run the twisted reactor
reactor.run()
# Will print out after we exit from the reactor loop
print '\nExecution completed'
# Print out the debugging data
print 'Application executed for %s seconds' % (
	round(reactor.seconds() - START_TIME, 3))
# Kill the process and get outta dodge
sys.exit(1)