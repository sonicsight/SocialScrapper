# -*- coding: utf-8 -*-
import cherrypy
import urllib
import math
import json
from sqlalchemy import func, desc, asc

from lib.model.tables import Region, Source, Term, Poster, Run, Record

__all__ = ["SocialScrapper"]

class SocialScrapper(object):
	@cherrypy.expose
	@cherrypy.tools.render(template="general.tmpl")
	def index(self):
		db = cherrypy.request.db
		data = {'dbStatus':'success',
				'dbMessage':'Ok',
				'dbIcon':'ok',
				'numRuns':0,
				'recTwitter':0,
				'recBlog': 0,
				'recTumblr': 0}
		if False:
			data['currentRun'] = 2
		data['numRuns'] = db.query(func.count(Run.Run_ID)).scalar()
		split = db.query(func.count(Record.Source_ID), Record.Source_ID).group_by(Record.Source_ID).all()
		for count, source in split:
			if source == 1:
				data['recTwitter'] = count
			if source == 2:
				data['recTumblr'] = count
			if source == 5:
				data['recBlog'] = count
		return data

	@cherrypy.expose
	@cherrypy.tools.render(template="run.tmpl")
	def recent(self, query=None):
		db = cherrypy.request.db
		lastRun = db.query(Run.Run_ID).order_by(desc(Run.Run_ID)).first()
		data = self.run(lastRun[0])
		data['isRecent'] = 'active'
		if query:
			data['alert'] = {'type':'alert-success', 'title':'Success!', 'body':'Search has been started for: "%s"'%query}
		return data

	@cherrypy.expose
	@cherrypy.tools.render(template="run.tmpl")
	def run(self, runId=1):
		if int(runId) < 1:
			runId = 1
		db = cherrypy.request.db
		data = {'runId':runId,
				'progress':0,
				'searchCrit':'(termA AND termB) AND termC',
				'timeStart':"2000-01-01 12:00:00",
				'timeEnd':'2000-01-01 12:00:00',
				'recTwitter':0,
				'recBlog': 0,
				'recTumblr': 0}
		run = db.query(Run).filter(Run.Run_ID == runId).one()
		if run.Status:
			data['progress'] = 100
		else:
			data['progress'] = 50
		data['timeStart'] = run.From_Time
		data['timeEnd'] = run.To_Time
		if run.Term1 and run.Term2 and run.Term3:
			data['searchCrit'] = '(%s %s %s) %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term, run.Operator2, run.Term3.Term)
		elif run.Term1 and run.Term2:
			data['searchCrit'] = '%s %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term)
		elif run.Term1:
			data['searchCrit'] = run.Term1.Term
		split = db.query(func.count(Record.Source_ID), Record.Source_ID).group_by(Record.Source_ID).filter(Record.Run_ID == runId).all()
		for count, source in split:
			if source == 1:
				data['recTwitter'] = count
			if source == 2:
				data['recTumblr'] = count
			if source == 5:
				data['recBlog'] = count
		return data

	@cherrypy.expose
	def check(self, runId=1):
		cherrypy.response.headers['Content-Type']= 'application/json'
		if int(runId) < 1:
			runId = 1
		db = cherrypy.request.db
		data = {'runId':runId,
				'progress':0,
				'searchCrit':'(termA AND termB) AND termC',
				'timeStart':"2000-01-01 12:00:00",
				'timeEnd':'2000-01-01 12:00:00',
				'recTwitter':0,
				'recBlog': 0,
				'recTumblr': 0}
		run = db.query(Run).filter(Run.Run_ID == runId).one()
		if run.Status:
			data['progress'] = 100
		else:
			stat = cherrypy.engine.publish('status-scrapper').pop()
			print stat
			prog = 0
			if stat['status'] == "success":
				prog = (float(stat['finished']) / float(stat['total'])) * 100.0
			data['progress'] = prog
		data['timeStart'] = str(run.From_Time)
		data['timeEnd'] = str(run.To_Time)
		if run.Term1 and run.Term2 and run.Term3:
			data['searchCrit'] = '(%s %s %s) %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term, run.Operator2, run.Term3.Term)
		elif run.Term1 and run.Term2:
			data['searchCrit'] = '%s %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term)
		elif run.Term1:
			data['searchCrit'] = run.Term1.Term
		split = db.query(func.count(Record.Source_ID), Record.Source_ID).group_by(Record.Source_ID).filter(Record.Run_ID == runId).all()
		for count, source in split:
			if source == 1:
				data['recTwitter'] = count
			if source == 2:
				data['recTumblr'] = count
			if source == 5:
				data['recBlog'] = count
		return json.dumps(data)


	@cherrypy.expose
	@cherrypy.tools.render(template="records.tmpl")
	def records(self, runId=1, page=1):
		if int(runId) < 1:
			runId = 1
		db = cherrypy.request.db
		count = db.query(func.count(Record.Record_ID)).filter(Record.Run_ID == runId).scalar()
		page = int(page)
		total = math.ceil(count/10.0)
		if page > total:
			page = total
		if page < 1:
			page = 1
		cur = page - 2
		pages = []
		while cur > total - 4:
			cur = cur-1
		if cur < 1:
			cur = 1
		for i in range(cur, cur+5):
			if i <= total:
				pages.append(i)
		offset = (page-1)*10
		limit = offset+10
		data = {'records':[], 'pages':{'current':page, 'total':total, 'pages':pages}, 'runId':runId}
		for record in db.query(Record).order_by(asc(Record.Record_ID)).filter(Record.Run_ID == runId)[offset:limit]:
			rregion = 'None'
			if record.Region:
				rregion = '(%s, %s)' % (record.Region.Latitude, record.Region.Longitude)
			data['records'].append({
				'recordId':record.Record_ID,
				'source':record.Source.Name,
				'region':rregion,
				'time':record.Time,
				'poster':unicode(record.Poster.Account, errors='ignore'),
				'text':unicode(record.Text, errors='ignore'),
				'link':record.Link
				})
		return data

	@cherrypy.expose
	@cherrypy.tools.render(template="history.tmpl")
	def history(self, page=1):
		db = cherrypy.request.db
		count = db.query(func.count(Run.Run_ID)).scalar()
		page = int(page)
		total = math.ceil(count/10.0)
		if page > total:
			page = total
		if page < 1:
			page = 1
		cur = page - 2
		pages = []
		while cur > total - 4:
			cur = cur-1
		if cur < 1:
			cur = 1
		for i in range(cur, cur+5):
			if i <= total:
				pages.append(i)
		offset = (page-1)*10
		limit = offset+10
		data = {'runs':[], 'pages':{'current':page, 'total':total, 'pages':pages}}
		for run in db.query(Run).order_by(desc(Run.Run_ID))[offset:limit]:
			rquery = ''
			if run.Term1 and run.Term2 and run.Term3:
				rquery = '(%s %s %s) %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term, run.Operator2, run.Term3.Term)
			elif run.Term1 and run.Term2:
				rquery = '%s %s %s' % (run.Term1.Term, run.Operator1, run.Term2.Term)
			elif run.Term1:
				rquery = run.Term1.Term
			rcount = db.query(func.count(Record.Record_ID)).filter(Record.Run_ID == run.Run_ID).scalar()
			rstatus = ''
			if run.Status:
				rstatus = 'Complete'
			else:
				rstatus = 'In Progress'
			data['runs'].append({
				'runId':run.Run_ID,
				'search':rquery,
				'count':rcount,
				'time':run.Time,
				'status':rstatus
				})
		return data

	@cherrypy.expose
	@cherrypy.tools.render(template="search.tmpl")
	def search(self, termA=None, termB=None, termC=None, operatorA=None, operatorB=None, fromDate=None, toDate=None):
		# show form to input new search
		query = ""
		if termA and termB and termC:
			query = "(%s %s %s) %s %s" % (termA, operatorA, termB, operatorB, termC)
		elif termA and termB:
			query = "%s %s %s" % (termA, operatorA, termB)
		elif termA:
			query = termA
		else:
			return
		status = cherrypy.engine.publish('start-scrapper', termA, termB, termC, operatorA, operatorB, fromDate, toDate).pop()
		if status['status'] == 'error':
			data['alert'] = {'type':'alert-danger', 'title':'Error!', 'body':'An error occured: "%s"'%status['error']}
			return data
		raise cherrypy.HTTPRedirect('/recent?'+urllib.urlencode({'query':query}))