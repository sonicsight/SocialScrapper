# -*- coding: utf-8 -*-
import cherrypy
from cherrypy.process import wspbus, plugins
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from lib.model import Base

__all__ = ['SAEnginePlugin']

class SAEnginePlugin(plugins.SimplePlugin):
	def __init__(self, bus, ip, port, user, pswd, db):
		plugins.SimplePlugin.__init__(self, bus)
		self.dbConfig = {
			'ip':ip,
			'port':port,
			'user':user,
			'pswd':pswd,
			'db':db
		}
		self.sa_engine = None
		self.session = scoped_session(sessionmaker(autoflush=True, autocommit=False))

	def start(self):
		self.bus.log('Starting up DB access')
		dbConfig = self.dbConfig
		self.sa_engine = create_engine('mysql://%s:%s@%s:%s/%s' % (dbConfig['user'], dbConfig['pswd'], dbConfig['ip'], dbConfig['port'], dbConfig['db']))
		self.create_all()
		self.bus.subscribe('bind-session', self.bind)
		self.bus.subscribe('commit-session', self.commit)

	def stop(self):
		self.bus.log('Shutting down DB access')
		self.bus.unsubscribe('bind-session', self.bind)
		self.bus.unsubscribe('commit-session', self.commit)
		if self.sa_engine:
			#self.destroy_all() # Will wipe all database data (bad idea)
			self.sa_engine.dispose()
			self.sa_engine = None

	def bind(self):
		self.session.configure(bind=self.sa_engine)
		return self.session

	def commit(self):
		try:
			self.session.commit()
		except:
			self.session.rollback()
			raise
		finally:
			self.session.remove()

	def create_all(self):
		self.bus.log('Creating database')
		from lib.model.tables import Region, Source, Term, Poster, Run, Record
		Base.metadata.create_all(self.sa_engine)

	def destroy_all(self):
		self.bus.log('Destroying database')
		Base.metadata.create_all(self.sa_engine)