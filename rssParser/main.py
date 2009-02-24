#!/usr/bin/env python

import wsgiref.handlers
import logging
import re
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
sectionCMSPath = re.compile(r'/?(.*)/[r|j].*$')

class MainHandler(webapp.RequestHandler):
	def getFeed(self):
		match = sectionCMSPath.search(self.request.path)
		if(match):
			rest_params = match.group(1)		
			logging.info("Rest params: " + rest_params)
			url = "http://www.guardian.co.uk/" + rest_params + "/rss"
			response = fetch(url)
			last_modified = response.headers['last-modified']
			logging.info("Last modified: " + last_modified)
			return response.content
		
