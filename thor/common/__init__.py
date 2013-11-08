import signal

from thor.common.signals import sighup_handler
from thor.common.signals import sigint_handler
#from thor.common.signals import sigkill_handler

signals = {
    # A non-invasive signal we will try to use this later for 
    # configuration reloading and such
    'sighup'  : {
        'signal' : signal.SIGHUP,
        'numeric': 1,
        'handler': 'sighup_handler'
    },
    # Shutdown without attempting to clean up any resources
    'sigkill' : {
        'signal' : signal.SIGKILL,
        'numeric': 9,
        'handler': 'sigkill_handler'
    },
    # Interrupt execution
    'sigint'  : {
        'signal' : signal.SIGINT,
        'numeric': 2,
        'handler': 'sigint_handler'
    },
    # For SIGTERM use the handler for SIGKILL
    'sigterm' : 'sigkill'
}

# Signal handler to handle the interrupt event
signal.signal(signal.SIGHUP, sighup_handler)
signal.signal(signal.SIGINT, sigint_handler)
#signal.signal(signal.SIGKILL, sigkill_handler)