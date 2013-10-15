import pycurl
import cStringIO

from thor import response

__HTTP_PORT__ = 80

PROXIES_TYPES_MAP = {
    'socks5': pycurl.PROXYTYPE_SOCKS5,
    'socks4': pycurl.PROXYTYPE_SOCKS4,
    'http': pycurl.PROXYTYPE_HTTP,
    'https': pycurl.PROXYTYPE_HTTP}

class Request(object):    
    
    def __init__(self, scheme = 'http', target = None, uri = None,
                 port = __HTTP_PORT__):
                     
        self.scheme = scheme
        self.target = target
        self._uri = uri
        self.port = port
        
        # initialize the cURL object
        self.__c_obj = pycurl.Curl()
        
        # Initialize the buffer that will contain the primary payload
        self.__r_buffer = cStringIO.StringIO()
        self.set_option(pycurl.WRITEFUNCTION, self.__payload)
        
        # Initialize the buffer that will contain the raw headers
        self.__r_header = cStringIO.StringIO()
        self.set_option(pycurl.HEADERFUNCTION, self.__header)
                
        # Extraneous variable settings
        self._proxy = None
        self.timeout = 30
        self.__follow = True
        self.__redirects = 1
        
        # class settings
        self.preserve_header = True
    
    def __del__(self):
        self.close()
        
    def __payload(self, payload):
        self.__r_buffer.write(payload)
        
    def __header(self, payload):
        self.__r_header.write(payload)
        
    def close(self, shutdown=False):
        # TODO shutdown vs. cleanup
        # Close the cURL object
        if (self.__c_obj):
            self.__c_obj.close()
        # Unset the cURL object handle
        self.__c_obj = None
        
        # close the buffers
        self.__r_header.close()
        self.__r_buffer.close()
        
    def get(self):
        self.set_option(pycurl.URL, self.url())
        
         # Execute the cURL request
        self.__c_obj.perform()
        
        # Save the buffer to close the resource
        buffer = self.__r_buffer.getvalue()
        header = self.__r_header.getvalue()
        
        # Create a new response object
        if (self.preserve_header):
            c_response = response.Response(self, self.__c_obj, r_buffer = buffer,
                r_header = header)
        else:
            c_response = response.Response(self, self.__c_obj, buffer)  
            
        return c_response
    
    def get_timeout(self):
        return self.__timeout
        
    def get_uri(self): 
        if (self._uri[0] is '/'):
            return self._uri[1:]
        return self._uri;
    
    def follow(self, opt=False):
        if (opt):
            self.__follow = opt
            self.set_option(pycurl.FOLLOWLOCATION, self.follow)
            
        elif (self.__follow):
            return 1
        
        else: return 0
    
    def redirects(self, opt=0):
        if (opt):
            self._redirects = opt  
            self.set_option(pycurl.MAXREDIRS, self.redirects)
            # Automatically allow redirects since we are allowing
            # multiple redirects (0 or more)
            if (opt > 0):
                self.follow(True)
                
        else: return self._redirects
        
    def url(self):
        if (self.port != 80):
            return '{scheme}://{target}:{port}/{uri}'.format(
                scheme = self.scheme, target = self.target, port = self.port,
                uri = self.get_uri())
                
        return '{scheme}://{target}/{uri}'.format(
                scheme = self.scheme, target = self.target, uri = self.get_uri())
                
    def post(self, post_data):
        print 'Posting a new request'
        
    def set_option(self, *args):
        self.__c_obj.setopt(*args)
        
    def set_timeout(self, timeout = 30):  
        # TODO verify this is actually numeric        
        self.__timeout = timeout
        self.set_option(pycurl.TIMEOUT, timeout)
        
    def set_uri(self, query_string):
        # TODO validate inputs
        self._uri = query_string
        
    def __str__(self):
        return self.url();
    
    # Property definitions for Request class
    follow = property(follow, follow)
    redirects = property(redirects, redirects)
    timeout = property(get_timeout, set_timeout)
    uri = property(get_uri, set_uri)
        
def request_factory():
    print 'Generating a factory request'