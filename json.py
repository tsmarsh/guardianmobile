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
import main
import time
from google.appengine.api.urlfetch import fetch

from google.appengine.ext import webapp

#time.struct_time
#(2009, 2, 10, 9, 9, 0, 1, 41, 0)

class ComplexEncoder(simplejson.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, time.struct_time):
			return time.strftime("%a, %d %b %Y %H:%M:%S +0000", obj)
		return simplejson.JSONEncoder.default(self, obj)
		
class JSONHandler(main.MainHandler):
	def get(self):
		content = self.getFeed()
		parsed_feed = simplejson.dumps(feedparser.parse(content), cls=ComplexEncoder)
		self.response.out.write(parsed_feed)

def main():
	application = webapp.WSGIApplication([('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
