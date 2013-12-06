from twisted.internet import reactor, defer

def getDummyData(x):
    d = defer.Deferred()
    # simulate a delayed result by asking the reactor to fire the
    # Deferred in 2 seconds time with the result x * 3
    reactor.callLater(2, d.callback, x * 3)
    return d

def printData(d):
    print 'd=%s' % d
    
def test(n):
    print 'n=%s' % n
    
    s = defer.Deferred()
    s.addCallback(stop)
    reactor.callLater(3, s.callback, 1) 
    
def stop(x):
    print 'Stopping reactor... (%s)' % x
    reactor.stop()

if __name__ == '__main__':
    d1 = defer.Deferred()
    d1.addCallback(test)
    
    print 'Calling getDummyData'
    d = getDummyData(3)
    print 'Calling addCallBack'
    d.addCallback(printData)
        
    reactor.callLater(1, d1.callback, 9 * 10)
 
    # start up the Twisted reactor (event loop handler) manually
    reactor.run()
    print 'Reactor shutdown'