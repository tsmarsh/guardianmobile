import wsgiref.handlers
import logging, unittest
import feedparser, simplejson, time
import main

from BeautifulSoup import BeautifulSoup

from google.appengine.ext import webapp

def _start_media_content(self, attrsD):
    context = self._getContext()
    context.setdefault('media_content', [])
    context['media_content'].append(attrsD)


def _start_media_thumbnail(self, attrsD):
    context = self._getContext()
    context.setdefault('media_thumbnail', [])
    self.push('url', 1) # new
    context['media_thumbnail'].append(attrsD)


def _end_media_thumbnail(self):
    url = self.pop('url')
    context = self._getContext()
    if url != None and len(url.strip()) != 0:
        if not context['media_thumbnail'][-1].has_key('url'):
            context['media_thumbnail'][-1]['url'] = url


feedparser._FeedParserMixin._start_media_content = _start_media_content
feedparser._FeedParserMixin._start_media_thumbnail = _start_media_thumbnail
feedparser._FeedParserMixin._end_media_thumbnail = _end_media_thumbnail

class ComplexEncoder(simplejson.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, time.struct_time):
			return time.strftime("%a, %d %b %Y %H:%M:%S +0000", obj)
		return simplejson.JSONEncoder.default(self, obj)
			
class JSONHandler(main.MainHandler):
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
		processed_feed['topStory'] = entries[0]
		processed_feed['leaders'] = entries[1:9]
		processed_feed['latest'] = entries[9:]
		return processed_feed
	
	def buildEntry(self, feedObject):
		entry = {}
		logging.debug("Parsing %s" % (feedObject['id']))
		entry['guid'] = feedObject['guid']
		entry['title'] = feedObject['title']
		entry['description'] = feedObject['summary_detail']['value']
		entry['date'] = feedObject['updated']
		entry['byline'] = feedObject['author']
		entry['type'] = feedObject['dc_type'].lower()
		entry['media'] = []
		if(feedObject.has_key('media_content')):
			for content in feedObject['media_content']:
				if content['type'].startswith("image"):
					if content['width'] == '140':
						entry['thumbnail'] = content
					else:
						entry['media'].append(content)
		return entry
			
	def remove_css(self, markup):
		soup = BeautifulSoup(markup)
		divs = soup.findAll()
		for div in divs:
			if div.has_key('style'):
				del(div['style'])
		
def main():
	application = webapp.WSGIApplication([('/.*/?json', JSONHandler)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
