import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from BeautifulSoup import BeautifulSoup
from guardianmobileinterface.model import Tag, Content, Picture

from guardianmobileinterface.settings import api_key
import re, logging, sys, urllib2, time

from google.appengine.ext import db
from guardianapi import Client, fetchers, errors

link_with_id_finder = re.compile(r".*/email/(\d+)")

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
				logging.info("Content is not in api, deleting")
				content.delete()
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
		logging.info("Working on: " + url)
		web_page = BeautifulSoup(urllib2.urlopen(url).read())
		id = self.parseId(web_page)
		if id:
			content.id = id
			self.parseContent(web_page, content)
			task = taskqueue.Task(url="/task/api", params={'key': content.put() })
			task.add(queue_name='api')
		else:
			content.delete()
		
def main():
	application = webapp.WSGIApplication([('/task/web', WebWorker), ('/task/api', APIWorker)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
