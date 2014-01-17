import multiprocessing

def threads(_processes=None):
     return int(2 * (_processes or processes()))

def processes():    
    return int(multiprocessing.cpu_count())

def system_data():
    return processes(), threads()