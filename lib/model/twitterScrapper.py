# -*- coding: utf-8 -*-
from lib.model.scrapper import Scrapper
import requests
from requests_oauthlib import OAuth1
from datetime import datetime
import cherrypy

class TwitterScrapper(Scrapper):
	Source_ID = 1
	search_url = 'https://api.twitter.com/1.1/search/tweets.json'

	CONSUMER_KEY = "XlUxPBbXo0bmVALJqw5WmQ"
	CONSUMER_SECRET = "tGFH7GKkbjrfUUxfsHmdECdlZsn2TENYiNwKWTqc"

	OAUTH_TOKEN = "744224750-tRWifUpPbkaVamO9gyTW18LfZBNhxAh4o9LBIRbJ"
	OAUTH_TOKEN_SECRET = "WpAYs16NyOvqUFedIV2yHRLm2eJjE5ZluXXK2hkpMk"

	def get_oauth(self):
		return OAuth1(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.OAUTH_TOKEN, self.OAUTH_TOKEN_SECRET)

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

	def build_link(self, user, tid):
		return 'https://twitter.com/%s/statuses/%s' % (user, tid)

	def run(self):
		db = self.get_db()
		q = self.build_query()
		count = 100
		since = self.fromDate
		until = self.toDate
		oauth = self.get_oauth()
		res = requests.get(self.search_url, params={'q':q, 'count':count, 'since':since, 'until':until}, auth=oauth)
		rjson = res.json()
		for status in rjson['statuses']:
			account = status['user']['screen_name']
			aid = self.add_poster(db, account)
			rid = None
			if status['coordinates'] and status['coordinates']['type'] == 'Point':
				lng = status['coordinates']['coordinates'][0]
				lat = status['coordinates']['coordinates'][1]
				rid = self.add_region(db, lat, lng)
			time = datetime.strptime(status['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
			text = status['text']
			link = self.build_link(account, status['id'])
			self.add_record(db, aid, rid, time, text, link)
		next = None
		if 'next_results' in rjson['search_metadata']:
			next = rjson['search_metadata']['next_results']
		while next:
			res = requests.get(self.search_url+next, auth=oauth)
			rjson = res.json()
			for status in rjson['statuses']:
				account = status['user']['screen_name']
				aid = self.add_poster(db, account)
				rid = None
				if status['coordinates'] and status['coordinates']['type'] == 'Point':
					lng = status['coordinates']['coordinates'][0]
					lat = status['coordinates']['coordinates'][1]
					rid = self.add_region(db, lat, lng)
				time = datetime.strptime(status['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
				text = status['text']
				link = self.build_link(account, status['id'])
				self.add_record(db, aid, rid, time, text, link)
			next = None
			if 'next_results' in rjson['search_metadata']:
				next = rjson['search_metadata']['next_results']
		self.close_db()
		cherrypy.engine.publish('scrapper-finish', self.Source_ID).pop()
