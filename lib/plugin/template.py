# -*- coding: utf-8 -*-
import cherrypy
from cherrypy.process import plugins
from jinja2 import Environment, FileSystemLoader

__all__ = ['Jinja2TemplatePlugin']

class Jinja2TemplatePlugin(plugins.SimplePlugin):
	def __init__(self, bus, base_dir=None, cache_size=50):
		plugins.SimplePlugin.__init__(self, bus)
		self.base_dir = base_dir
		self.cache_size = cache_size
		self.env = None

	def start(self):
		self.bus.log('Setting up Jinja2 resources')
		self.env = Environment(loader=FileSystemLoader(self.base_dir), cache_size=self.cache_size)
		self.bus.subscribe("lookup-template", self.get_template)

	def stop(self):
		self.bus.log('Freeing Jinja2 resources')
		self.bus.unsubscribe("lookup-template", self.get_template)
		self.env = None

	def get_template(self, name):
		return self.env.get_template(name)