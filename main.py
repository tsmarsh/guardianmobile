#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




import wsgiref.handlers
import logging
import feedparser
import simplejson
import StringIO
from google.appengine.api.urlfetch import fetch

from google.appengine.ext import webapp

class MainHandler(webapp.RequestHandler):
	def getFeed(self):
		rest_params = self.request.path.split('/')
		logging.info("Rest params: " + str(rest_params))
		if len(rest_params) > 2:
			section = rest_params[1]
			url = "http://www.guardian.co.uk/" + section + "/rss"
		else:
			url = "http://www.guardian.co.uk/rss"
		return fetch(url)
		
class JSONHandler(MainHandler):
	def get(self):
		content = fetch(url).content
		self.response.out.write(content)

class RSSHandler(MainHandler):
	def get(self):
		logging.info("Request path:\t" + self.request.path)
		self.response.out.write(self.getFeed().content)

def main():
	application = webapp.WSGIApplication([('/.*/?rss', RSSHandler),('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
