#import socket
#import time

#from threading import current_thread
from threading import Event
from threading import RLock
from threading import Thread
from threading import ThreadError

# Service headers

__SERVICE_THREADS__ = 'system'
__POOL_THREADS__    = 'pool'

# Logging / Debug Levels
__S_DEBUG__ = 1
__S_INFO__  = 2
__S_ERROR__ = 3

class Service(object):  
    
    def __init__(self, config, delay = 1, num_threads = 1):
        # We first need to instantiate a lock object that will be used 
        # to synchronize all of the properties for this service 
        self.__lock = RLock()  
               
        # Container to hold the threads
        self.__threads = {
            # Contains system threads for service level operations
            # Such as the changing of operations and cleanup, etc
            __SERVICE_THREADS__ : {},
            # Contains a pool of threads that we manage with this 
            # application
            __POOL_THREADS__    : {}
        }
        
        # Thread pooling properties
        self.__num_threads = num_threads
        self.__delay_start = delay
        
        # Thread Pool status controller
        self.__status = Event()
        self.__status.set()
        
        # Print out an initialized message
        print 'Service loaded'
    
    
    def get_delay(self):
        return self.__delay_start
    
    def init(self):
        pass
    
    def interrupt(self, timeout = 1):
        self.__lock.acquire()
        try:
            # Step one is to shutdown the Service which is processing
            # the new threads
            self.__status.set()
            
            # TODO provide a time based option for shutting down
            
            # Join each thread as we shutdown this will end
            # their processing
            for group in self.__threads.keys():
                for thread in self.__threads[group]:
                    # Save the thread name for use later (We're overwriting it next)
                    thread_name = thread
                    # We need to reference what thread we are actually working
                    # with right now since this is a multi-dimensional list
                    thread = self.__threads[group][thread]
                    # AN error is thrown if the thread has not been started
                    # we want to prevent this here and just move on to killing it
                    if (thread.isAlive()):
                        continue
                    # First step is to join the thread with the give timeout
                    # By default 1 second is the initial timeout to wait
                    thread.join(timeout)
                    # AFter we have joined the thread we check to make sure it
                    # was actually ended properly
                    if (thread.isAlive()):
                        # Houston we have a problem.
                        raise ThreadError
        finally:
            self.__lock.release()
    
    def lock(self):
        return self.__lock
    
    def is_running(self):
        self.__lock.acquire()
        try:
            # If the status event is set then we are
            # either not currently running or have shutdown
            if self.__status.is_set():
                return False
            # We're running, so keep it simple
            return True
        finally:
            self.__lock.release()
    
    def set_delay(self, delay):
        self.__lock.acquire()
        try:
            self.__delay_start = delay
        finally:
            self.__lock.release() 
            
    # The delay between the initialization of one thread to the next
    # This value is in seconds
    delay = property(get_delay, set_delay)    