# -*- coding: utf-8 -*-
import cherrypy
from cherrypy.process import plugins
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

from lib.model import twitterScrapper, blogScrapper, tumblrScrapper
from lib.model.tables import Source, Region, Term, Poster, Run, Record

__all__ = ['ScrapperPlugin']

class ScrapperPlugin(plugins.SimplePlugin):
	def __init__(self, bus):
		plugins.SimplePlugin.__init__(self, bus)
		self.scrappers = []
		self.curRun = None
		self.curCount = 0

	def start(self):
		self.bus.log('Launching Scrapper Manager')
		self.bus.subscribe("start-scrapper", self.start_scrapper)
		self.bus.subscribe("status-scrapper", self.status_scrapper)
		self.bus.subscribe("scrapper-finish", self.scrapper_finish)
		self.bus.subscribe("scrapper-record", self.scrapper_record)

	def stop(self):
		self.bus.log('Closing Scrapper Manager')
		self.bus.unsubscribe("start-scrapper", self.start_scrapper)
		self.bus.unsubscribe("status-scrapper", self.status_scrapper)
		self.bus.unsubscribe("scrapper-finish", self.scrapper_finish)
		self.bus.unsubscribe("scrapper-record", self.scrapper_record)

	def start_scrapper(self, termA=None, termB=None, termC=None, operatorA=None, operatorB=None, fromDate=None, toDate=None):
		if self.curRun:
			return {'status': 'error', 'error': 'Only one scrapper can run at a time.'}
		# contact db server and create new run
		db = cherrypy.engine.publish('bind-session').pop()
		ta_id = self.add_term(db, termA)
		tb_id = self.add_term(db, termB)
		tc_id = self.add_term(db, termC)
		run = Run(ta_id, tb_id, tc_id, operatorA, operatorB, fromDate, toDate, datetime.now(), False)
		db.add(run)
		db.commit()
		self.curRun = run.Run_ID
		self.curCount = 1
		tws = twitterScrapper.TwitterScrapper(self.bus, run.Run_ID, termA, termB, termC, operatorA, operatorB, fromDate, toDate)
		bls = blogScrapper.BlogScrapper(self.bus, run.Run_ID, termA, termB, termC, operatorA, operatorB, fromDate, toDate)
		tus = tumblrScrapper.TumblrScrapper(self.bus, run.Run_ID, termA, termB, termC, operatorA, operatorB, fromDate, toDate)
		self.scrappers = [tws, bls, tus]
		for scrapper in self.scrappers:
			scrapper.start()
		cherrypy.engine.publish('commit-session')
		return {'status':'success'}

	def status_scrapper(self):
		if not self.curRun:
			return {'status': 'error', 'error': 'No scrappers currently running'}
		count = 0
		for scrapper in self.scrappers:
			if not scrapper.isAlive():
				count = count + 1
		return {'status': 'success', 'finished': count, 'total': len(self.scrappers)}

	def scrapper_finish(self, sourceId=None):
		count = 0
		for scrapper in self.scrappers:
			if not scrapper.isAlive() or scrapper.Source_ID == sourceId:
				count = count + 1
		if count == len(self.scrappers):
			self.scrappers = []
			db = cherrypy.engine.publish('bind-session').pop()
			run = db.query(Run).filter(Run.Run_ID == self.curRun).one()
			run.Status = True
			cherrypy.engine.publish('commit-session')
			self.curRun = None
			self.curCount = 0

	def scrapper_record(self):
		c = self.curCount
		if c > 0:
			self.curCount = c+1
		return c

	def add_term(self, db, term):
		if not term:
			return None
		curTerm = None
		try:
			curTerm = db.query(Term).filter(Term.Term == term).one()
			curTerm.Last_Search = datetime.now()
		except NoResultFound:
			curTerm = Term(term, datetime.now())
			db.add(curTerm)
		finally:
			db.commit()
			return curTerm.Term_ID



