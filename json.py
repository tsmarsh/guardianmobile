import wsgiref.handlers
import logging, unittest
import feedparser, simplejson, time
import main

from google.appengine.api.urlfetch import fetch
from BeautifulSoup import BeautifulSoup

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
		cleaned_feed = self.clean(feedparser.parse(content))
		self.response.out.write(self.pythonToJson(cleaned_feed))
	
	def pythonToJson(self, obj):
		return simplejson.dumps(obj, cls=ComplexEncoder)
		
	def clean(self, feed):
		for entry in feed['entries']:
			self.remove_css(entry['summary_detail']['value'])
		return feed
	
	def remove_css(self, markup):
		soup = BeautifulSoup(markup)
		divs = soup.findAll()
		for div in divs:
			if div.has_key('style'):
				del(div['style'])

class Tests(unittest.TestCase):

	def setUp(self):
		self.jsonHandler = JSONHandler()
	
	def testShouldConvertPythonObjectsToJson(self):
		stub = {'time': (2004, 1, 1, 12, 30, 2, 0, 0, 0), 'detail': "monkey"}
		json = self.jsonHandler.pythonToJson(stub)
		print json;
		
def main():
	application = webapp.WSGIApplication([('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
