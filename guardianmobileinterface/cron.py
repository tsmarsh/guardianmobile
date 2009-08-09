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
	'high': [
				{"path": "", 	"link_text" : "Front page"}, 
				{"path": "/uk", "link_text" : "UK news"}, 
				{"path": "/world",	"link_text" :"World news"}, 
				{"path": "/sport", 	"link_text" : "Sport"}, 
				{"path": "/football", 	"link_text" : "Football"},
			],
	'moderate': [
			{"path": "/politics", 	"link_text" :  "Politics"}, 
			{"path": "/world/usa", 	"link_text" :  "USA News"}, 
			{"path": "/film", 	"link_text" :  "Film"}, 
			{"path": "/music", 	"link_text" :  "Music"}, 
				],
	'low': [
		{"path": "/science", 	"link_text" :   "Science"}, 
		{"path": "/technology", 	"link_text" :   "Technology"}, 
		{"path": "/environment", 	"link_text" :   "Environment"}, 
		{"path": "/travel", 	"link_text" :   "Travel"}, 
		{"path": "/culture", 	"link_text" :   "Culture"}, 
		{"path": "/society", 	"link_text" :   "Society"}],
	}


class RSSFeedChecker(webapp.RequestHandler):

	def get(self, feed_path):
		feeds = all_feeds[feed_path]
		
		for feed in feeds:
			feed_item = Feed.all().filter('path =', feed['path']).fetch(1)
			if feed_item:
				feed_item = feed_item[0]
				feed_item.content = []
			else:
				feed_item = Feed(content =[], path = feed['path'])
				
			key = feed_item.put()
			taskqueue.add(url='/task/rss', params={'key': key, 'url': root % feed['path']})
			
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
