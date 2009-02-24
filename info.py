import wsgiref.handlers
import os
from google.appengine.ext import webapp

class InfoHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write("hello!")
		for name in os.environ.keys():
			self.response.out.write("%s = %s<br />\n" % (name, os.environ[name]))

def main():
	application = webapp.WSGIApplication([('/info', InfoHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)
