import os
import sys

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__),
                                   os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from thor import request, response, service
from thor.common import utils



# Modify these values to control how the testing is done

# How many threads should be running at peak load.
num_threads = 10

# How many minutes the test should run with all threads active.
time_at_peak = 100 # seconds

# How many seconds to wait between starting threads.
# Shouldn't be set below 30 seconds.
delay_between_thread_start = 1 # seconds

if __name__ == '__main__':
    thor = service.Asgard(num_threads=num_threads, time_at_peak=time_at_peak, delay_between_thread_start=delay_between_thread_start)
    thor.execute()
    print "Finished"
    