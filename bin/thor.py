import os
import sys
import socket
import time

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__),
                                   os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'thor', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from thor import request, response, service
from thor.common import utils
from threading import Event
from threading import Thread
from threading import current_thread


# Modify these values to control how the testing is done

# How many threads should be running at peak load.
NUM_THREADS = 2

# How many minutes the test should run with all threads active.
TIME_AT_PEAK_QPS = 120 # seconds

# How many seconds to wait between starting threads.
# Shouldn't be set below 30 seconds.
DELAY_BETWEEN_THREAD_START = 5 # seconds

quitevent = Event()

def threadproc():
    """This function is executed by each thread."""
    print "Thread started: %s" % current_thread().getName()
    thread_name = current_thread().getName()
    while not quitevent.is_set():
        try:
                scheme = 'http'
                target = 'phantomnet.net'
                uri = '/'
                r = request.Request(scheme=scheme, target=target, uri=uri)  
                curl_response = r.get()
                print '[RESPONSE times=%s]' % curl_response.times()
                print thread_name
        except socket.timeout:
            pass

    print "Thread finished: %s" % current_thread().getName()
 
if __name__ == '__main__':
    runtime = (TIME_AT_PEAK_QPS + DELAY_BETWEEN_THREAD_START * NUM_THREADS)
    print "Total runtime will be: %d seconds" % runtime
    threads = []
    try:
        for i in range(NUM_THREADS):
            t = Thread(target=threadproc)
            t.start()
            threads.append(t)
            time.sleep(DELAY_BETWEEN_THREAD_START)
        print "All threads running"
        time.sleep(TIME_AT_PEAK_QPS)
        print "Completed full time at peak qps, shutting down threads"
    except:
        print "Exception raised, shutting down threads"

    quitevent.set()
    time.sleep(3)
    for t in threads:
        t.join(1.0)
    print "Finished"