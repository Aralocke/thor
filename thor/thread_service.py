import socket
import time
from threading import Event
from threading import Thread
from threading import current_thread
from thor import request, response

class Asgard(object):
    def __init__(self, num_threads, time_at_peak, delay_between_thread_start):
        self.num_threads = num_threads
        self.time_at_peak = time_at_peak 
        self.delay_between_thread_start = delay_between_thread_start
        self.quitevent = Event()
        self. req_generated = 0
        print 'Service is loaded!'
        
    def service_method(self):
        print 'Service method'
        
    def threadproc(self):
        #This function is executed by each thread
        print "Thread started: %s" % current_thread().getName()
        thread_name = current_thread().getName()
        while not self.quitevent.is_set():
            try:
                    scheme = 'http'
                    target = 'perpetual-fusion.com'
                    uri = '/'
                    r = request.Request(scheme=scheme, target=target, uri=uri)  
                    curl_response = r.get()
                    print '[RESPONSE times=%s]' % curl_response.times()
                    r.close()
                    counter = 0
                    self.req_generated += 1
                    print thread_name, ' ',  self.req_generated

            except socket.timeout:
                pass

        print "Thread finished: %s" % current_thread().getName()
        
    def execute(self):
        
        runtime = (self.time_at_peak + self.delay_between_thread_start * self.num_threads)
        print "Total runtime will be: %d seconds" % runtime
        threads = []
        try:
            
            for i in range(self.num_threads):
                t = Thread(target=self.threadproc)
                t.start()
                threads.append(t)
                time.sleep(self.delay_between_thread_start)
            print "All threads running"
            time.sleep(self.time_at_peak)
            print "Completed full time at peak qps, shutting down threads"
        except:
            print "Exception raised, shutting down threads"

        self.quitevent.set()
        time.sleep(3)
        for t in threads:
            t.join(1.0)
        
def make_service():
    service = TestService()
    return service
