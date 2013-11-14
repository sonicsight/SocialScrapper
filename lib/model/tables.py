# -*- coding: utf-8 -*-
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER as Integer, DATETIME as DateTime, VARCHAR as String, DECIMAL as Decimal, BOOLEAN as Boolean, CHAR as Character
from sqlalchemy import desc
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref

from lib.model import Base

__all__ = ['Poster', 'Region', 'Source', 'Run', 'Term', 'Record']

class Source(Base):
	__tablename__ = 'Dimension_Source'
	Source_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Name = Column(String(100), nullable=False)
	URL = Column(String(100), nullable=False)

	def __init__(self, name, url):
		self.Name = name
		self.URL = url

	def __repr__(self):
		return "<Source ('%s', '%s, '%s')>" % (self.Source_ID, self.Name, self.URL)

class Region(Base):
	__tablename__ = 'Dimension_Region'
	Region_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Latitude = Column(Decimal(precision=11, scale=8, unsigned=False), nullable=False)
	Longitude = Column(Decimal(precision=11, scale=8, unsigned=False), nullable=False)

	def __init__(self, lat, lng):
		self.Latitude = lat
		self.Longitude = lng

	def __repr__(self):
		return "<Region ('%s', '%s', '%s')>" % (self.Region_ID, self.Latitude, self.Longitude)

class Term(Base):
	__tablename__ = "Dimension_Term"
	Term_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Term = Column(String(100), nullable=False)
	First_Search = Column(DateTime(), nullable=False)
	Last_Search = Column(DateTime, nullable=False)

	def __init__(self, term, time):
		self.Term = term
		self.First_Search = time
		self.Last_Search = time

	def __repr__(self):
		return "<Term ('%s', '%s', '%s', '%s')>" % (self.Term_ID, self.Term, self.First_Search, self.Last_Search)

class Poster(Base):
	__tablename__ = 'Dimension_Poster'
	Poster_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Source_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Source.Source_ID'), nullable=False)
	Account = Column(String(120), nullable=False)
	First_Post = Column(DateTime(), nullable=False)
	Last_Post = Column(DateTime(), nullable=False)

	Source = relationship("Source", backref=backref('Posters', order_by=Poster_ID))

	def __init__(self, source, account, time):
		self.Source_ID = source
		self.Account = account
		self.First_Post = time
		self.Last_Post = time

	def __repr__(self):
		return "<Poster ('%s', '%s', '%s', '%s', '%s')>" % (self.Poster_ID, self.Source_ID, self.Account, self.First_Post, self.Last_Post)

class Run(Base):
	__tablename__ = 'Dimension_Run'
	Run_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Term1_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Term.Term_ID'), nullable=False)
	Term2_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Term.Term_ID'), nullable=True)
	Term3_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Term.Term_ID'), nullable=True)
	Operator1 = Column(Character(10), nullable=True)
	Operator2 = Column(Character(10), nullable=True)
	From_Time = Column(DateTime(), nullable=False)
	To_Time = Column(DateTime(), nullable=False)
	Time = Column(DateTime(), nullable=False)
	Status = Column(Boolean(), nullable=False)

	Term1 = relationship("Term", backref=backref('Run_Terms1', order_by=Run_ID), foreign_keys=[Term1_ID])
	Term2 = relationship("Term", backref=backref('Run_Terms2', order_by=Run_ID), foreign_keys=[Term2_ID])
	Term3 = relationship("Term", backref=backref('Run_Terms3', order_by=Run_ID), foreign_keys=[Term3_ID])

	def __init__(self, t1, t2, t3, o1, o2, ft, tt, time, status):
		self.Term1_ID = t1
		self.Term2_ID = t2
		self.Term3_ID = t3
		self.Operator1 = o1
		self.Operator2 = o2
		self.From_Time = ft
		self.To_Time = tt
		self.Time = time
		self.Status = status

	def __repr__(self):
		return "<Run ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % (self.Run_ID, self.Term1_ID, self.Term2_ID, self.Term3_ID, self.Operator1, self.Operator2, self.From_Time, self.To_Time, self.Time, self.Status)

class Record(Base):
	__tablename__ = 'Fact_Record'
	Record_ID = Column(Integer(unsigned=True), nullable=False, primary_key=True)
	Run_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Run.Run_ID'), nullable=False)
	Poster_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Poster.Poster_ID'), nullable=False)
	Source_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Source.Source_ID'), nullable=False)
	Region_ID = Column(Integer(unsigned=True), ForeignKey('Dimension_Region.Region_ID'), nullable=True)
	Run_Position = Column(Integer(unsigned=True), nullable=False)
	Time = Column(DateTime(), nullable=False)
	Text = Column(String(255), nullable=False)
	Link = Column(String(100), nullable=False)

	Run = relationship("Run", backref=backref('Records', order_by=Record_ID))
	Poster = relationship("Poster", backref=backref('Records', order_by=Record_ID))
	Source = relationship("Source", backref=backref('Records', order_by=Record_ID))
	Region = relationship("Region", backref=backref('Records', order_by=Record_ID))

	def __init__(self, run, poster, source, region, pos, time, text, link):
		self.Run_ID = run
		self.Poster_ID = poster
		self.Source_ID = source
		self.Region_ID = region
		self.Run_Position = pos
		self.Time = time
		self.Text = text
		self.Link = link

	def __repr__(self):
		return "<Record ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % (self.Record_ID, self.Run_ID, self.Poster_ID, self.Source_ID, self.Region_ID, self.Run_Position, self.Time, self.Text, self.Link)