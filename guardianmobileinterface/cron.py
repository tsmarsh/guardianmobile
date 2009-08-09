# -*- coding: utf-8 -*-
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
import urllib2, logging, re
from guardianmobileinterface.model import Feed, Content
from google.appengine.ext import db
from datetime import datetime, timedelta

root = "http://www.guardian.co.uk%s/rss"

all_feeds = {
	'high': ["", "/uk", "/world", "/sport", "/football"],
	'moderate': ["/politics", "/world/usa", "/film", "/music" ],
	'low': ["/science", "/technology", "/environment", "/travel", "/culture", "/society"]
}


class RSSFeedChecker(webapp.RequestHandler):

	def get(self, feed_path):
		feeds = all_feeds[feed_path]
		
		for feed in feeds:
			feed_item = Feed.all().filter('path =', feed).fetch(1)
			if feed_item:
				feed_item = feed_item[0]
				feed_item.content = []
			else:
				feed_item = Feed(content = [], path = feed)
				
			key = feed_item.put()
			
			taskqueue.add(url='/task/rss', params={'key': key, 'url': root % feed})

			feed_item.put()
			
class DeleteOldContent(webapp.RequestHandler):
	def get(self):
		logging.info("Deleting old content")
		old_content = Content.all().filter('publication_date >', datetime.now() - timedelta(-1))
		
		count = 0
		for content in old_content:
			count = count + 1
			taskqueue.add(url='/task/deleteold', params={'key': content.key()})
			
		logging.info("Marked %d content for deletion" % count)
	
def main():
	application = webapp.WSGIApplication([(r'/cron/feeds/(.*)', RSSFeedChecker),
										(r'/cron/remove_old', DeleteOldContent)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
