# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
from datetime import datetime
from time import mktime
import unittest, logging

class RSSParser():
	date_format = "%a, %d %b %Y %H:%M:%S %Z"
	
	namespaces = {
		'dc' : "{http://purl.org/dc/elements/1.1/}",
		'media' : '{http://search.yahoo.com/mrss/}'
	}
	
	def parse_item_media(self, item_tree):
		media = {}
		thumbnail = {}
		pictures = []
		contents = item_tree.findall(self.namespaces['media']+'content')
		for content in contents:
			if len(thumbnail) == 0 and content.get('width') == '140':
				thumbnail['url'] = content.get('url')
				thumbnail['alttext'] = content.findtext(self.namespaces['media']+'description')
				thumbnail['credit'] = content.findtext(self.namespaces['media']+'credit')
				media['thumbnail'] = thumbnail
			else:
				picture = {}
				picture['url'] = content.get('url')
				picture['alttext'] = content.findtext(self.namespaces['media']+'description')
				picture['credit'] = content.findtext(self.namespaces['media']+'credit')
				pictures.append(picture)
		
		media['pictures'] = pictures
		return media
	
	def parse_item(self, item_tree):
		item = {}
		item['guid'] = item_tree.findtext('guid')[len("http://www.guardian.co.uk/"):].replace('/', '-')
		pub_date = item_tree.findtext('pubDate')
		if pub_date:		
			logging.debug("Parsing item: " + item['guid'])
			item['title'] = item_tree.findtext('title')
			item['date'] = pub_date
			item['sysdate'] = mktime(datetime.strptime(pub_date, self.date_format).timetuple())
			item['description'] = item_tree.findtext('description')
			item['creator'] = item_tree.findtext(self.namespaces['dc']+'creator')
			item.update( self.parse_item_media(item_tree))
			return item
		else:
			logging.error("Item: %s has no publicaton date" % item['guid'])
		
	def parse(self, xml):
		feed = {}
		items = []
		rsstree = ET.parse(xml)
		for item in rsstree.findall('/channel/item'):
			parsed_item = self.parse_item(item)
			if parsed_item:
				items.append(self.parse_item(item))
		feed['content'] = items
		return feed

class RSSParserTest(unittest.TestCase):
	def setUp(self):
		self.parser = RSSParser()
		
	def testCanParseOutGUIDFromASingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals("http://www.guardian.co.uk/society/2009/feb/06/haringey-social-services-ed-balls", feed['leaders'][0]['guid'])
		
	def testCanParseOutTitleFromASingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"'Reckless' minister has put children at risk – Shoesmith", feed['leaders'][0]['title'])
		
	def testCanParseOutPublicationDateFromASingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"Sat, 07 Feb 2009 01:26:00 GMT", feed['leaders'][0]['date'])
		
	def testCanParseOutCreatorFromASingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"Patrick Butler", feed['leaders'][0]['creator'])
		
	def testCanParseOutDescriptionFromSingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals(191, feed['leaders'][0]['description'].find('Shoesmith'))
		
	def testCanParseOutThumbnailFromSingleRSSEntry(self):
		testXML = open('test/singleItemRss.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals({
		'url':u'http://static.guim.co.uk/sys-images/Guardian/Pix/pictures/2009/2/6/1233946444750/Sharon-Shoesmith-former-D-003.jpg', 
		'alttext':u'Sharon Shoesmith, former Director of Child Services at Haringey Council.  Photograph: Sarah Lee/Guardian', 
		'credit': u'Sarah Lee/Guardian'},   feed['leaders'][0]['thumbnail'])
		
	def testCanParseOutGUIDFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals("http://www.guardian.co.uk/society/2009/feb/06/haringey-social-services-ed-balls",   feed['leaders'][0]['guid'])

	def testCanParseOutTitleFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"'Reckless' minister has put children at risk – Shoesmith",   feed['leaders'][0]['title'])

	def testCanParseOutPublicationDateFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"Sat, 07 Feb 2009 00:01:00 GMT",   feed['leaders'][6]['date'])

	def testCanParseOutCreatorFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals( u"John Hooper",   feed['leaders'][3]['creator'])

	def testCanParseOutDescriptionFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals(191, feed['leaders'][0]['description'].find('Shoesmith'))
		
	def testCanParseOutThumbnailFromAnRSSEntry(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals({
		'url':u'http://static.guim.co.uk/sys-images/Guardian/Pix/pictures/2009/2/6/1233946444750/Sharon-Shoesmith-former-D-003.jpg', 
		'alttext':u'Sharon Shoesmith, former Director of Child Services at Haringey Council.  Photograph: Sarah Lee/Guardian', 
		'credit': u'Sarah Lee/Guardian'},   feed['leaders'][0]['thumbnail'])
		
	def testCanParseOutAllFirst10ItemsFromAFeedIntoLeaders(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals(10, len(feed['leaders']))
		
	def testCanParseOutAllTheRemainderInToLatest(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals(25, len(feed['latest']))
	
	def testCanParseOutAllPictures(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertEquals(15, len(feed['latest'][4]['pictures']))
		
	def testTheTwoListsDontOverlap(self):
		testXML = open('test/networkfront.xml', 'r')
		feed = self.parser.parse(testXML)
		self.assertFalse(feed['latest'][0]['guid'] == feed['leaders'][9]['guid'])
		
	
if __name__ == '__main__':
	unittest.main()