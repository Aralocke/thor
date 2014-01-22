class BufferedConnection(object):

    delimeter = '\r\n'
    bufflen = 16384
    __buffer = ''

    def clearLineBuffer(self):
	    # Clear the buffered data
	    _buffer, self.__buffer = self.__buffer, ''                
	    # return the data that was in the buffer for clean up purposes
	    return _buffer