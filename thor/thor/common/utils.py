NO_PROCESS_ERR = -1

def has_multiprocessing():
    try:
        import multiprocessing
    except (ImportError, NotImplementedError):
        return False
    
    return True

def num_threads():
    threads = 2 * num_processes()
    
    if threads < 0:
        return NO_PROCESS_ERR
    
    return threads

def num_processes():    
    if not has_multiprocessing:
        return NO_PROCESS_ERR
    
    import multiprocessing
    return multiprocessing.cpu_count()

def system_data():
    # The default data here "should" be equivalent to the constant
    # from the variable NO_PROCESS_ERR if something happened and the
    # library we need isn't installed
    processes, threads = num_processes(), num_threads()
    
    if processes is NO_PROCESS_ERR:
        processes = 1
    
    if threads is NO_PROCESS_ERR:
        threads = 4
    
    return (processes, threads)