# -*- coding: utf-8 -*-
from lib.model.scrapper import Scrapper
import requests
from datetime import datetime
import cherrypy

class BlogScrapper(Scrapper):
	Source_ID = 5
	search_url = 'https://ajax.googleapis.com/ajax/services/search/blogs'

	def conv_op(self, op):
		if op == 'AND':
			return ' AND '
		if op == 'OR':
			return ' OR '
		if op == 'NOT':
			return " -"
		if op == 'Append':
			return ' '

	def build_query(self):
		if self.numTerms == 1:
			return '"%s"' % self.termA
		if self.numTerms == 2:
			return '"%s"%s"%s"' % (self.termA, self.conv_op(self.operatorA), self.termB)
		if self.numTerms == 3:
			return '"%s"%s"%s"%s"%s"' % (self.termA, self.conv_op(self.operatorA), self.termB, self.conv_op(self.operatorB), self.termC)

	def recheck(self, text):
		if self.termA in text:
			return True
		if self.numTerms >= 2 and self.termB in text and self.operatorA != 'NOT':
			return True
		if self.numTerms >= 3 and self.termC in text and self.operatorB != 'NOT':
			return True
		return False

	def run(self):
		db = self.get_db()
		q = self.build_query()
		count = 8
		res = requests.get(self.search_url, headers={'referer':'http://socialscrapper.com/'}, params={ 'v':'1.0', 'q':q, 'rsz':count, 'scoring':'d', 'start':'0'})
		rjson = res.json()
		for post in rjson['responseData']['results']:
			if not self.recheck(post['content']):
				continue
			account = post['author']
			aid = self.add_poster(db, account)
			rid = None
			time = datetime.strptime(post['publishedDate'][:-6],'%a, %d %b %Y %H:%M:%S')
			text = post['content']
			link = post['postUrl']
			self.add_record(db, aid, rid, time, text, link)
		if 'cursor' in rjson['responseData']:
			for page in rjson['responseData']['cursor']['pages']:
				if int(page['start']) == 0:
					continue
				res = requests.get(self.search_url, headers={'referer':'http://socialscrapper.com/'}, params={ 'v':'1.0', 'q':q, 'rsz':count, 'scoring':'d', 'start':page['start']})
				rjson = res.json()
				for post in rjson['responseData']['results']:
					if not self.recheck(post['content']):
						continue
					account = post['author']
					aid = self.add_poster(db, account)
					rid = None
					time = datetime.strptime(post['publishedDate'][:-6],'%a, %d %b %Y %H:%M:%S')
					text = post['content']
					link = post['postUrl']
					self.add_record(db, aid, rid, time, text, link)
		self.close_db()
		cherrypy.engine.publish('scrapper-finish', self.Source_ID).pop()