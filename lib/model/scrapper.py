# -*- coding: utf-8 -*-
import threading
import cherrypy
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

from lib.model.tables import Source, Region, Term, Poster, Run, Record

class Scrapper(threading.Thread):
	Source_ID = 0
	runId = 0

	def __init__(self, bus, runId, termA=None, termB=None, termC=None, operatorA=None, operatorB=None, fromDate=None, toDate=None):
		threading.Thread.__init__(self)
		self.bus = bus
		self.runId = runId
		self.termA = termA
		self.termB = termB
		self.termC = termC
		self.operatorA = operatorA
		self.operatorB = operatorB
		self.fromDate = fromDate
		self.toDate = toDate
		if termA and termB and termC:
			self.numTerms = 3
		elif termA and termB:
			self.numTerms = 2
		elif termA:
			self.numTerms = 1
		else:
			self.numTerms = 0

	def run(self):
		cherrypy.engine.publish('scrapper-finish', self.Source_ID).pop()

	def get_db(self):
		return cherrypy.engine.publish('bind-session').pop()

	def close_db(self):
		cherrypy.engine.publish('commit-session')

	def add_region(self, db, lat, lng):
		if lat == None or lng == None:
			return None
		curRegion = None
		try:
			curRegion = db.query(Region).filter(Region.Latitude == lat).filter(Region.Longitude == lng).one()
		except NoResultFound:
			curRegion = Region(lat, lng)
			db.add(curRegion)
		finally:
			db.commit()
			return curRegion.Region_ID

	def add_poster(self, db, account):
		if account == None:
			return None
		curPoster = None
		try:
			curPoster = db.query(Poster).filter(Poster.Account == account.encode('ascii','ignore')).filter(Poster.Source_ID == self.Source_ID).one()
			curPoster.Last_Post = datetime.now()
		except NoResultFound:
			curPoster = Poster(self.Source_ID, account.encode('ascii','ignore'), datetime.now())
			db.add(curPoster)
		finally:
			db.commit()
			return curPoster.Poster_ID

	def add_record(self, db, poster, region, time, text, link):
		pos = cherrypy.engine.publish('scrapper-record').pop()
		rec = Record(self.runId, poster, self.Source_ID, region, pos, time, text.encode('ascii','ignore'), link)
		db.add(rec)
		return rec.Record_ID
