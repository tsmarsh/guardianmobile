#!/usr/bin/env python

import wsgiref.handlers
import logging
import main

from google.appengine.ext import webapp

class RSSHandler(main.MainHandler):
	def get(self):
		logging.info("Request path:\t" + self.request.path)
		self.response.out.write(self.getFeed())

def main():
	application = webapp.WSGIApplication([('/.*/?rss', RSSHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
