# -*- coding: utf-8 -*-
from lib.model.scrapper import Scrapper
import requests
import cherrypy
import parsedatetime.parsedatetime as pdt
from datetime import datetime

class TumblrScrapper(Scrapper):
	Source_ID = 2
	search_url = 'https://www.googleapis.com/customsearch/v1'

	API_KEY = ""
	CSE_ID = ""
	FIELDS = "queries(nextPage/startIndex),items(link,displayLink,snippet)"

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

	def run(self):
		db = self.get_db()
		q = self.build_query()
		count = 10
		cal = pdt.Calendar()
		res = requests.get(self.search_url, params={
			'q':q,
			'key':self.API_KEY,
			'cx':self.CSE_ID,
			'fields':self.FIELDS,
			'num':count,
			'sort':'date',
			'filter':'1'
			})
		rjson = res.json()
		if 'items' in rjson:
			for post in rjson['items']:
				account = post['displayLink'].split('.')[0]
				aid = self.add_poster(db, account)
				rid = None
				pt = cal.parse(post['snippet'].split(' ... ')[0])
				time = datetime(pt[0][0],pt[0][1],pt[0][2],pt[0][3],pt[0][4],pt[0][5])
				text = post['snippet'][post['snippet'].find(' ... ')+len(' ... '):]
				link = post['link']
				self.add_record(db, aid, rid, time, text, link)
		next = None
		if 'queries' in rjson:
			next = rjson['queries']['nextPage'][0]['startIndex']
		while next:
			res = requests.get(self.search_url, params={
				'q':q,
				'key':self.API_KEY,
				'cx':self.CSE_ID,
				'fields':self.FIELDS,
				'num':count,
				'start':next,
				'sort':'date',
				'filter':'1'
				})
			rjson = res.json()
			for post in rjson['items']:
				account = post['displayLink'].split('.')[0]
				aid = self.add_poster(db, account)
				rid = None
				pt = cal.parse(post['snippet'].split(' ... ')[0])
				time = datetime(pt[0][0],pt[0][1],pt[0][2],pt[0][3],pt[0][4],pt[0][5])
				text = post['snippet'][post['snippet'].find(' ... ')+len(' ... '):]
				link = post['link']
				self.add_record(db, aid, rid, time, text, link)
			next = None
			if 'queries' in rjson:
				next = rjson['queries']['nextPage'][0]['startIndex']
				if (int(next)+count) > 101:
					next = None
		self.close_db()
		cherrypy.engine.publish('scrapper-finish', self.Source_ID).pop()