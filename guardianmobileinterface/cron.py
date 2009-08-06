# -*- coding: utf-8 -*-
import wsgiref.handlers
from xml.etree import ElementTree as ET
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
import urllib2, logging, re
from guardianmobileinterface.model import Content, Picture, Feed
from datetime import datetime
from time import mktime
from google.appengine.ext import db

root = "http://www.guardian.co.uk%s/rss"

all_feeds = {
	'high': ["", "/uk", "/world", "/sport", "/football"],
	'moderate': ["/politics", "/world/usa", "/film", "/music" ],
	'low': ["/science", "/technology", "/environment", "/travel", "/culture", "/society"]
}

class RSSFeedChecker(webapp.RequestHandler):
	"""Should run every 10 mins"""

	date_format = "%a, %d %b %Y %H:%M:%S %Z"
	
	def parse_item_media(self, item, content_item):
		contents = item.findall('{http://search.yahoo.com/mrss/}content')
		for content in contents:
			picture = Picture()
			picture.url = db.Link(content.get('url'))
			picture.alt_text = db.Text(content.findtext('{http://search.yahoo.com/mrss/}description'))
			picture.credit = content.findtext('{http://search.yahoo.com/mrss/}credit')
			picture.put()
			
			if content.get('width') == '140':
				content_item.thumbnail = picture
			else:	
				content_item.pictures.append(picture.key())
	
	def buildContent(self, item):
		content = Content()	
		pub_date = item.findtext('pubDate')
		if pub_date:
			content.publication_date = datetime.strptime(pub_date, self.date_format)
		content.web_url = db.Link(item.findtext('link'))
		self.parse_item_media(item, content)
		return content	
	
	def get(self):
		match = re.search(r'/cron/feeds/(.*)', self.request.path)
		if not match:
			return
		feeds = all_feeds[match.group(1)]
		
		for feed in feeds:
			feed_item = Feed.all().filter('path =', feed).fetch(1)
			if feed_item:
				feed_item = feed_item[0]
			else:
				feed_item = Feed(content = [], path = feed)
		
			
			logging.info(root % feed)
			rsstree = ET.parse(urllib2.urlopen(root % feed))
			for item in rsstree.findall('/channel/item'):
				content = Content.all().filter('web_url =', item.findtext('link')).fetch(1)
				if not content:
					content = self.buildContent(item)
					key = content.put()
					feed_item.content.append(key)
					taskqueue.add(url='/task/web', params={'key': key})
				else:
					content = content[0]
					feed_item.content.append(content.put())
				feed_item.put()
		
def main():
	application = webapp.WSGIApplication([(r'/cron/feeds/.*', RSSFeedChecker)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
