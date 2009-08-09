#!/usr/bin/env python
# encoding: utf-8
#!/usr/bin/env python
# encoding: utf-8

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
import simplejson, re, logging

from guardianmobileinterface.model import Feed, Content
from datetime import datetime
from guardianmobileinterface.cron import all_feeds
host = "http://superguardianmobile.appspot.com"

class ComplexEncoder(simplejson.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%a, %d %b %Y %H:%M:%S +0000")
		return simplejson.JSONEncoder.default(self, obj)

class JSONOutputHandler(webapp.RequestHandler):
	def returnJSON(self, json):
		callback = self.request.get('callback')
		if callback:
			self.response.out.write("%s ( " % callback)
		simplejson.dump(json, self.response.out, cls=ComplexEncoder)
		if callback:
			self.response.out.write(" )")
	
class DetailHandler(JSONOutputHandler):
	extract_content_id = r'/api/detail/(\d+)'
	
	def buildPicture(self, picture_id):
		json = {}
		picture = db.get(picture_id)
		json['url'] = picture.url
		json['alt_text'] = picture.alt_text
		json['credit'] = picture.credit
		return json
	
	def buildPictures(self, pictures):
		pictures = []
		for key in pictures:
			pictures.append(self.buildPicture(key))
		return pictures
		
	def buildTag(self, tag_id):
		json = {}
		tag = db.get(tag_id)
		json['filter'] = tag.filter
		json['web_url'] = tag.webUrl
		json['type'] = tag.type
		json['name'] = tag.name
		return json
	
	def buildTags(self, tags):
		tags = []
		for key in tags:
			tags.append(self.buildTag(key))
		return tags
	
	def buildContent(self, content_id):
		json = {}
		content = Content.all().filter('id =', content_id).fetch(1)[0]
		json['id'] = content_id
		json['byline'] = content.byline
		json['publication'] = content.publication
		json['section_name'] = content.section_name 
		json['headline'] = content.headline
		json['web_url'] = content.web_url
		json['trail_text'] = content.trail_text
		json['link_text'] = content.link_text
		json['type'] = content.type
		json['body'] = content.body
		json['publication_date'] = content.publication_date
			
		json['tags'] = self.buildTags(content.tags)
		
		json['pictures'] = self.buildPictures(content.pictures)	
		
		return json
	
	def get(self, id):
		json = {}
		json = self.buildContent(id)
			
		self.returnJSON(json)
		
class SummaryHandler(JSONOutputHandler):
	extract_content_id = r'/api/summary/(\d+)'
	detail_url = host + "/api/detail/"
	
	def buildPicture(self, picture):
		if not picture:
			return
		json = {}
		json['url'] = picture.url
		json['alt_text'] = picture.alt_text
		json['credit'] = picture.credit
		return json
		
	def get(self, id):
		json_content = {}
		content = Content.all().filter('id =', id).fetch(1)[0]
		json_content['id'] = id
		json_content['headline'] = content.headline
		json_content['thumbnail'] = self.buildPicture(content.thumbnail)
		json_content['summary'] = content.trail_text
		json_content['detail_url'] = self.detail_url + id
		json_content['section_name'] = content.section_name
		
		self.returnJSON(json_content)
		
class ListHandler(JSONOutputHandler):
	
	summary_url = host + "/api/summary/"	

	def get(self, feed_name):
		json_feed = []
		feed_name = feed_name or ""
		
		feed = Feed.all().filter("path =", feed_name).fetch(1);
		if feed:
			feed = feed[0]
			for content in feed.content:
				content_item = db.get(content)
				if content_item and content_item.section_name:
					json_feed.append(self.summary_url + content_item.id)
				else: 
					if content_item:
						logging.info("Content item: %s is not ready" % content_item.web_url)
					else:
						logging.info("Content item missing in action")
		else: 
			logging.info("Couldn't find feed: %s" % feed_name)
		
		self.returnJSON(json_feed)

class MetaListHandler(JSONOutputHandler):
			
	def get(self):
		json = []
		
		for _, list_of_endpoints in all_feeds.iteritems():
			for endpoint in list_of_endpoints:
				json.append(
					{"path" :		host + "/api/list" + endpoint['path'], 
					'link_text':	endpoint['link_text'], }
				)
		
		self.returnJSON(json)

			
def main():
	application = webapp.WSGIApplication(
		[(r'/api/?', MetaListHandler),
		(r'/api/list(/?.*)', ListHandler), 
		(r'/api/summary/(\d+)', SummaryHandler),
		(r'/api/detail/(\d+)', DetailHandler)], debug=True)
		
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()