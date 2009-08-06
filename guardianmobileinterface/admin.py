import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from guardianmobileinterface.model import Feed, Content, Tag, Picture

class ResetDataStore(webapp.RequestHandler):
	
	def get(self):
		entities = [Feed, Content, Tag, Picture]
		for entity in entities:
			for item in entity.all():
				item.delete()
		print "Success"

def main():
	application = webapp.WSGIApplication([(r'/admin/reset', ResetDataStore)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()