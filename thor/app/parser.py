import optparse
from optparse import BadOptionError, AmbiguousOptionError

class OptionParser(optparse.OptionParser):

	# Solution provided by Stack Overflow found via Google
	# Link: http://stackoverflow.com/a/9307174
	 def _process_args(self, largs, rargs, values):
		while rargs:
			try:
				optparse.OptionParser._process_args(self,largs,rargs,values)
			except (BadOptionError,AmbiguousOptionError), e:
				largs.append(e.opt_str)