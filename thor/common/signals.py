def sighup_handler(signal, frame):
    import sys
    # TODO Cool alert message
    print 'SIGHUP recieved'
    
def sigint_handler(signal, frame):
    import sys
    # TODO Cool alert message
    print 'SIGINT recieved'
    # When we recieve the interrupt signal, exit out and
    # get outta dodge    
    sys.exit(0)
    
def sigkill_handler(signal, frame):
    import os
    import signal
    # TODO Cool alert message
    print 'SIGKILL recieved'
    # When we recieve the interrupt signal, exit out and
    # get outta dodge    
    os.kill(os.getpid(), signal.SIGKILL)