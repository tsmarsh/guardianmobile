import wsgiref.handlers
import logging, unittest, re
import feedparser, simplejson, time
import main
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import fetch

from BeautifulSoup import BeautifulSoup

from google.appengine.ext import webapp

sectionCMSPath = re.compile(r'/?(.*)/[r|j].*$')

def _start_media_content(self, attrs):
    context = self._getContext()
    context.setdefault('media_content', [])
    context['media_content'].append(attrs)


def _start_media_thumbnail(self, attrs):
    context = self._getContext()
    context.setdefault('media_thumbnail', [])
    self.push('url', 1) # new
    context['media_thumbnail'].append(attrs)


def _end_media_thumbnail(self):
    url = self.pop('url')
    context = self._getContext()
    if url != None and len(url.strip()) != 0:
        if not context['media_thumbnail'][-1].has_key('url'):
            context['media_thumbnail'][-1]['url'] = url

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
			logging.info("Rest params: " + rest_params)
			url = "http://www.guardian.co.uk/" + rest_params + "/rss"
			response = fetch(url)
			last_modified = response.headers['last-modified']
			logging.info("Last modified: " + last_modified)
			cached_response = memcache.get(url)
			if cached_response:
				if cached_response.headers['last-modified'] == last_modified:
					logging.info("Found matching request in cache")
					return cached_response.content
				else:
					logging.info("Newer content found storing %s in cache" % url)
					memcache.set(url, response, 600)
					return response.content
			else:
				logging.info("Storing %s in cache" % url)
				memcache.set(url, response, 600)
				return response.content
				
	def get(self):
		content = self.getFeed()
		logging.debug('Got feed')
		cleaned_feed = self.clean(feedparser.parse(content))
		logging.debug('Parsed and cleaned')
		self.response.out.write(self.pythonToJson(cleaned_feed))
		logging.debug('Request completed')
	
	def pythonToJson(self, obj):
		return simplejson.dumps(obj, cls=ComplexEncoder)
		
	def clean(self, feed):
		entries = []
		processed_feed = {}
		for entry in feed['entries']:
			#self.remove_css(entry['summary_detail']['value'])
			entries.append(self.buildEntry(entry))
		processed_feed['leaders'] = entries[:9]
		processed_feed['latest'] = entries[9:]
		return processed_feed
	
	def buildEntry(self, feedObject):
		entry = {}
		logging.debug("Parsing %s" % (feedObject['id']))
		cached_entry = memcache.get(feedObject['guid'])
		if(cached_entry):
			return cached_entry
		else:
			entry['guid'] = feedObject['guid']
			entry['title'] = feedObject['title']
			entry['description'] = feedObject['summary_detail']['value']
			entry['date'] = feedObject.get('updated', "")
			entry['byline'] = feedObject.get('author', "")
			entry['type'] = feedObject.get('dc_type', "").lower()
			entry['media'] = []
			if(feedObject.has_key('media_content')):
				for content in feedObject['media_content']:
					if content['type'].startswith("image"):
						if content['width'] == '140':
							entry['thumbnail'] = content
						else:
							entry['media'].append(content)
			memcache.set(entry['guid'], entry, 1200)
		return entry
			
	def remove_css(self, markup):
		soup = BeautifulSoup(markup)
		divs = soup.findAll()
		for div in divs:
			if div.has_key('style'):
				del(div['style'])
		
def main():
	feedparser._FeedParserMixin._start_media_content = _start_media_content
	feedparser._FeedParserMixin._start_media_thumbnail = _start_media_thumbnail
	feedparser._FeedParserMixin._end_media_thumbnail = _end_media_thumbnail
	application = webapp.WSGIApplication([('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
