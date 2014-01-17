from thor.common.core import server

class TCPServer(server.Server):

	def __init__(self, iface='0.0.0.0', port='21189'):
		# Initialize the base server classes
		server.Server.__init__(self)
		# Save these as none here so that there is ALWAYS a reference to the
		# variables. After wards we can call the method, and know there will
		# ALWAYS be a reference
		self.iface = None
		self.port = None
		# Logic for setting and saving the interface and port are all located in 
		# one place rather then several
		self.setInterface( iface=iface, port=port )

	def setInterface(self, iface=None, port=None):
		if iface is not None:
			self.iface = str(iface)

		if port is not None:
			self.port = int(port) 