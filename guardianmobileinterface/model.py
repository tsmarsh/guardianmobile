from google.appengine.ext import db

class Feed(db.Model):
	content = db.ListProperty(db.Key)
	path = db.StringProperty()
	last_modified = db.StringProperty()
	
class Tag(db.Model):
	filter = db.StringProperty(multiline=True)
	webUrl = db.LinkProperty()
	type = db.StringProperty(multiline=True)
	name = db.StringProperty(multiline=True)
	api_url = db.LinkProperty()

class Picture(db.Model):
	url = db.LinkProperty()
	alt_text = db.TextProperty()
	credit = db.StringProperty(multiline=True)
	
class Content(db.Model):
	byline = db.StringProperty(multiline=True)
	publication = db.StringProperty(multiline=True)
	section_name = db.StringProperty()
	headline = db.StringProperty(multiline=True)
	web_url = db.LinkProperty()
	api_url = db.LinkProperty()
	trail_text = db.StringProperty(multiline=True)
	link_text = db.StringProperty(multiline=True)
	type = db.StringProperty()
	id = db.StringProperty()
	body = db.TextProperty()
	tags = db.ListProperty(db.Key)
	pictures = db.ListProperty(db.Key)
	thumbnail = db.ReferenceProperty(Picture)
	publication_date = db.DateTimeProperty()