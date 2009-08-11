import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from BeautifulSoup import BeautifulSoup
from guardianmobileinterface.model import Tag, Content, Picture, Feed
from xml.etree import ElementTree as ET
from datetime import datetime

from guardianmobileinterface.settings import api_key
import re, logging, sys, urllib2, time

from google.appengine.ext import db
from guardianapi import Client, fetchers, errors

link_with_id_finder = re.compile(r".*/email/(\d+)")


#Many thanks to the Django team for this snippet.
url_re = re.compile(
	r'^https?://' # http:// or https://
	r'(?:(?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6}|' #domain...
	r'localhost|' #localhost...
	r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
	r'(?::\d+)?' # optional port
	r'(?:/?|/\S+)$', re.IGNORECASE)
	
	
class APIWorker(webapp.RequestHandler):
	"""Grabs the meta data using the id
	completion of this task marks the story for publishing
	"""
	
	def post(self):
		content = db.get(self.request.get('key'))
		if not content:
			logging.info("Content has been deleted, bailing")
			return
		
		logging.info("Working on: %s (%s)" % (content.web_url, content.id))
		api_item = None
		client = Client(api_key)
		
		for _ in range(8):
			try:
				api_item = client.item(content.id)
				break
			except fetchers.HTTPError, e:
				logging.error("Status code: %d\tDetails: %s" % (e.status_code, e.info))
				logging.info("Content is not in api, bailing")
				return
			except errors.APIKeyError, e:
				logging.error("API being hit too hard")
				time.sleep(1)
			
		if api_item.has_key('byline'):
			content.byline = api_item['byline']
		if not content.publication_date:
			content.publication_date = api_item['publicationDate'] 
		content.publication = api_item['publication']
		content.section_name = api_item['sectionName']
		content.headline = api_item['headline']
		content.api_url = db.Link(api_item['apiUrl'])
		content.trail_text = api_item['trailText']
		content.link_text = api_item['linkText']
		content.type = api_item['type']
		content.tags = []
		
		for tag in api_item['tags']:
			if not Tag.all().filter('filter =', tag['filter']).fetch(1):
				new_tag = Tag()
				new_tag.filter = tag['filter']
				if tag['webUrl']:
					new_tag.web_url = db.Link(tag['webUrl'])
				new_tag.type = tag['type']
				new_tag.name = tag['name']
				new_tag.api_url = db.Link(tag['apiUrl'])
				new_tag.put()
				content.tags.append(new_tag.key())
		
		content.put()
		
class WebWorker(webapp.RequestHandler):
	"""Grabs the id and the content for a given url, 
		puts the url and id on the API worker queue.
	"""
	
	
	def parseId(self, web_page):
		matching_links = web_page.findAll('a', href=link_with_id_finder)
		if matching_links:
			return link_with_id_finder.match(matching_links[0]['href']).group(1)
			
	def parseContent(self, web_page, content):
		body = web_page.findAll('div', id="article-wrapper")
		if body:
			content.body = db.Text(unicode(body[0]))
		
	def post(self):
		content = db.get(self.request.get('key'))
		if not content:
			logging.info("Content has been deleted, bailing")
			return
		
		url = content.web_url
		if not url_re.match(url):
			logging.info("Sent bad url, bailing and removing task: " + url)
			return #bogus url bail and remove task
			
		logging.info("Working on: " + url)
		
		web_page = BeautifulSoup(urllib2.urlopen(url).read())
		id = self.parseId(web_page)
		if id:
			#no id, no progress, api responsible for checking content is valid
			content.id = id
			self.parseContent(web_page, content)
			task = taskqueue.Task(url="/task/api", params={'key': content.put() })
			task.add(queue_name='api')

class RSSWorker(webapp.RequestHandler):

	date_format = "%a, %d %b %Y %H:%M:%S %Z"

	def parse_item_media(self, item, content_item):
		media = item.findall('{http://search.yahoo.com/mrss/}content')
		for content in media:
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
	
	def post(self, path):
		feed_item = db.get(self.request.get('key'))
		url = self.request.get('url')
		
		#Errors in cron.py can reach herem this can probably be removed later
		if not url_re.match(url):
			logging.info("Sent bad url, bailing and removing task: " + url)
			return #bogus url bail and remove task
			
		logging.info("Working on: %s:\t%s" % (path, url))
		rss_feed = None
		
		#Check to see if an update is required
		if feed_item.last_modified:
			req = urllib2.Request(url, headers={'if-modified-since' : feed_item.last_modified})
			try:
				rss_feed = urllib2.urlopen(req)
			except urllib2.HTTPError, e:
				logging.info("RSS still valid for: " + path)
				return #rss not updated: win!
		else:
			rss_feed = urllib2.urlopen(url)
			
		feed_item.last_modified = rss_feed.headers['date']	
		feed_item.content = []
		#process the feed
		for event, elem in ET.iterparse(rss_feed):
			if elem.tag == "item":
				link = elem.findtext("link")
				if re.search(r'guardian.co.uk', link):
					content = Content.all().filter('web_url =', link).fetch(1)
					if not content:
						content = self.buildContent(elem)
						key = content.put()
						feed_item.content.append(key)
						taskqueue.add(url='/task/web', params={'key': key})
					else:
						content = content[0]
						feed_item.content.append(content.put())
					elem.clear() # won't need the children any more
				else:
					logging.info("None guardian url, bailing (%s)" % link)
					content.delete()
				
		feed_item.put()

class DeleteOldContentWorker(webapp.RequestHandler):
	"""Required because """
	def post(self):
		content = db.get(self.request.get('key'))
		if content:
			logging.info("Deleting content: %s" % content.web_url)
			if content.thumbnail:
				content.thumbnail.delete()
			for tag in content.tags:
				tag.delete()
			for picture in content.pictures:
				picture.delete()
			
			content.delete()
		
def main():
	application = webapp.WSGIApplication(
		[(r'/task/web', WebWorker), 
		(r'/task/api', APIWorker),
		(r'/task/rss(.*)', RSSWorker),
		(r'/task/deleteold', DeleteOldContentWorker)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
