# -*- coding: utf-8 -*-
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
import urllib2, logging, re
from guardianmobileinterface.model import Feed, Content
from google.appengine.ext import db
from datetime import datetime, timedelta

root = "http://www.guardian.co.uk%s/rss"

all_feeds = [
	{"path": "", 				"link_text" : "Front page", 		"zone" : "news"}, 
	{"path": "/uk",				"link_text" : "UK news", 			"zone" : "news"}, 
	{"path": "/world/usa", 		"link_text" : "USA News", 			"zone" : "news"},
	{"path": "/world",			"link_text" : "World news", 		"zone" : "news"}, 
	{"path": "/politics", 		"link_text" : "Politics", 			"zone" : "politics"},
	{"path": "/science", 		"link_text" : "Science",			"zone" : "science"}, 
	{"path": "/technology",		"link_text" : "Technology", 		"zone" : "science"},
	{"path": "/environment",	"link_text" : "Environment", 		"zone" : "technology"},
	{"path": "/society", 		"link_text" : "Society", 			"zone" : "society"}, 
	{"path": "/business",		"link_text" : "Business", 			"zone" : "business"},
	{"path": "/money",			"link_text" : "Money", 				"zone" : "money"},
	{"path": "/sport", 			"link_text" : "Sport", 				"zone" : "sport"}, 
	{"path": "/football", 		"link_text" : "Football", 			"zone" : "sport"}, 
	{"path": "/film", 			"link_text" : "Film", 				"zone" : "film"},
	{"path": "/music", 			"link_text" : "Music", 				"zone" : "music"},
	{"path": "/culture", 		"link_text" : "Culture", 			"zone" : "culture"},  
	{"path": "/lifeandstyle",	"link_text" : "Life and style",		"zone" : "lifeandstyle"},
	{"path": "/travel", 		"link_text" : "Travel", 			"zone" : "travel"}, 
	]


class RSSFeedChecker(webapp.RequestHandler):
		
	def get(self):
		for feed in all_feeds:
			feed_item = Feed.all().filter('path =', feed['path']).fetch(1)
			key = None
			if feed_item:
				feed_item = feed_item[0]
				key = feed_item.key()
			else:
				feed_item = Feed(content =[], path = feed['path'])
				key = feed_item.put()
			taskqueue.add(url='/task/rss'+feed['path'], params={'key': key, 'url': root % feed['path']})
			
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
	application = webapp.WSGIApplication([(r'/cron/feeds', RSSFeedChecker),
										(r'/cron/remove_old', DeleteOldContent)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
