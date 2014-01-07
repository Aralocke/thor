from twisted.web import resource, server

class RootResource(resource.Resource):
	pass

class WebSite(server.Site):
	def __init__(self, path, *args, **kwargs):
		root = RootResource()
		server.Site.__init__(self, path, *args, **kwargs)