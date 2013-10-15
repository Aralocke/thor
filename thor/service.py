class TestService(object):
    def __init__(self):
        print 'Service is loaded!'
        
    def service_method(self):
        print 'Service method'
        
def make_service():
    service = TestService()
    return service