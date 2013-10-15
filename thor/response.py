import pycurl

from thor.common import utils

class Response(object):
    
    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols', 'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted', 'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices', 'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified', 'Document has not changed since given time'),
        305: ('Use Proxy', 'You must use proxy specified in Location to access this resource.'),
        307: ('Temporary Redirect', 'Object moved temporarily -- see URI list'),

        400: ('Bad Request', 'Bad request syntax or unsupported method'),
        401: ('Unauthorized', 'No permission -- see authorization schemes'),
        402: ('Payment Required', 'No payment -- see charging schemes'),
        403: ('Forbidden', 'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed', 'Specified method is invalid for this server.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone', 'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable', 'Cannot satisfy request range.'),
        417: ('Expectation Failed', 'Expect condition could not be satisfied.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented', 'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable', 'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout', 'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }
    
    timed_metrics = {
        'dns-lookup': 'Time required to perform a DNS lookup',
        'connection': 'Time required to initialize the connection',
        'appconnect': 'Time required to connect to the application',
        'pretransfer': 'Time required to initialize pre-transfer routines',
        'transfer': 'Time required to recieve the response',
        'total': 'Total time to initialize, connect, and recieve a response',
        'redirects': 'Total time to navigate redirections',
    }
    
    def __init__(self, request_obj = None, c_obj = None, r_buffer = None, r_header = None):
        # We set the request object here as the parent value
        self.__request = request_obj
        
        # Set the HTTP response values from the passed curl object response
        self.__status = c_obj.getinfo(pycurl.HTTP_CODE)
        
        # Save the passed buffer
        self.__buffer = r_buffer
        self.__header = r_header
        
        # Grab the time based values and save to a dictionary
        __total_time = 0
        # perform() --> NAMELOOKUP --> CONNECT --> APPCONNECT
        #           --> PRETRANSFER --> STARTTRANSFER --> TOTAL 
        #           --> REDIRECT 
        self.__time = {}
        # DNS lookup starts at zero
        self.__time['dns-lookup'] = round(utils.zero(c_obj.getinfo(pycurl.NAMELOOKUP_TIME)), 5)
        __total_time += self.__time['dns-lookup']
        # Remove the DNS lookup from the connection initialization time
        self.__time['connection'] = round(utils.zero(c_obj.getinfo(pycurl.CONNECT_TIME) - __total_time), 5)
        __total_time += self.__time['connection']
        # Removing the initialization times from app connect
        self.__time['appconnect'] = round(utils.zero(c_obj.getinfo(pycurl.APPCONNECT_TIME) - __total_time), 5)
        __total_time += self.__time['appconnect']
        # COnnection has been initialized, stripping data out
        self.__time['pretransfer'] = round(utils.zero(c_obj.getinfo(pycurl.PRETRANSFER_TIME) - __total_time), 5)
        __total_time += self.__time['pretransfer']
        # COnnection to outbound server is being established
        self.__time['transfer'] = round(utils.zero(c_obj.getinfo(pycurl.STARTTRANSFER_TIME) - __total_time), 5)
        __total_time += self.__time['transfer']
        # Total time to finish the first request
        # Does NOT include the redirect times .. so it's in fact not the 'total'
        self.__time['total'] = round(c_obj.getinfo(pycurl.TOTAL_TIME), 5)       
        # Redirection occurs when a location header is found 
        self.__time['redirect'] = round(utils.zero(c_obj.getinfo(pycurl.REDIRECT_TIME) - self.__time['total']), 5)

    def buffer(self):
        return self.__buffer
    
    def header(self):
        return self.__header
    
    def status(self):
        return self.__status    
    
    def __str__(self):
        return '[Response]'