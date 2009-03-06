import wsgiref.handlers
import logging, re
import simplejson, time
from StringIO import StringIO
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import fetch
from rssParser.rssparser import RSSParser

from google.appengine.ext import webapp

sectionCMSPath = re.compile(r'/?(.*)/json$')

class ComplexEncoder(simplejson.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, time.struct_time):
			return time.strftime("%a, %d %b %Y %H:%M:%S +0000", obj)
		return simplejson.JSONEncoder.default(self, obj)
				
class JSONHandler(webapp.RequestHandler):
		
	def getFeed(self):
		match = sectionCMSPath.search(self.request.path)
		if(match):
			rest_params = match.group(1)		
			self.url = "http://www.guardian.co.uk/" + rest_params + "/rss"
			logging.info("Fetching: " + self.url)
			response = StringIO(fetch(self.url).content)
			return response
			
	def get(self):
		feed = self.getFeed()
		logging.debug('Got feed')
		cleaned_feed = RSSParser().parse(feed)
		logging.debug('Parsed and cleaned')
		self.response.out.write(self.pythonToJson(cleaned_feed))
		logging.debug('Request completed')
	
	def pythonToJson(self, obj):
		return simplejson.dumps(obj)
			
def main():
	application = webapp.WSGIApplication([('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
