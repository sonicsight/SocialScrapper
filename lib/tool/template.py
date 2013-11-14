# -*- coding: utf-8 -*-
import os.path

import cherrypy
from jinja2 import Template, TemplateError

__all__ = ['Jinja2Tool']

class Jinja2Tool(cherrypy.Tool):
	def __init__(self):
		cherrypy.Tool.__init__(self, 'before_finalize', self._render, priority=30)

	def _render(self, template=None, debug=False):
		if cherrypy.response.status > 399:
			return

		# retrive data from the handler
		data = cherrypy.response.body or {}
		template = cherrypy.engine.publish("lookup-template", template).pop()

		if template and isinstance(data, dict):
			# dump the template using the dictionary
			if debug:
				try:
					cherrypy.response.body = template.render(**data)
				except TemplateError as e:
					cherrypy.response.body = e.message
			else:
				cherrypy.response.body = template.render(**data)