class Metric(object):

    def __init__(self, metric):
        self.metric = metric
        self.calls = 0

    def trigger(self, *args, **kwargs):
    	# Keep track of the number of calls to this method we get
    	self.calls += 1
    	# The args and kwargs args represent the values that are sent to the
    	# decorated method. We have the opportunity to view them here and
    	# translate them into metrics or data that can be reported back

    def __call__(self, callable):    	
		# We have two copies of the self variable. One represent the
		# physical metric instance we create in the decorator, the other
		# is the 'self' object of the class we are wrapping
		def wrapped(*args, **kwargs):
			# Allert the metric that we have triggered a processing point. 
			# The value of self at this point represents the actual metric 
			# and not the class we are calling from
			self.trigger(*args, **kwargs)
			# Now we can call the callable function of our decorator
			callable(*args, **kwargs)
		# Retruning the wrapped function which is calling the actual 
		# decorated function within the class
		return wrapped

def metric(target):
	m = Metric(target)
	return m