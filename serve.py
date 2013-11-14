# -*- coding: utf-8 -*-
import sys
import os, os.path
import logging
from logging import handlers

import cherrypy
from cherrypy import _cplogging
from cherrypy.lib import httputil

default_conf = "server.cfg"

class Server(object):
    def __init__(self, basedir, conf_file):
        # Set up the application directories
        self.base_dir = basedir
        self.conf_dir = os.path.join(self.base_dir, 'conf')
        self.log_dir = os.path.join(self.base_dir, 'logs')
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        # Set global configs
        cherrypy.config.update(os.path.join(self.conf_dir, conf_file))
        #cherrypy.config.update({'error_page.default': self.on_error})

        # Add the base dir to the path so we can import modules
        sys.path.insert(0, self.base_dir)

        # Template engine tool
        from lib.tool.template import Jinja2Tool
        cherrypy.tools.render = Jinja2Tool()

        # Database access tool
        from lib.tool.db import SATool
        cherrypy.tools.db = SATool()

        # The Application
        from webapp.app import SocialScrapper
        app = cherrypy.tree.mount(SocialScrapper(), '/', os.path.join(self.conf_dir, 'app.cfg'))
        # Prevent app level logs
        app.log.error_file = ""
        app.log.access_file = ""
        # Make a global level rotating log (app logs bubble up to here)
        self.make_rotate_logs()

        # Template engine plugin
        from lib.plugin.template import Jinja2TemplatePlugin
        cherrypy.engine.jinja2 = Jinja2TemplatePlugin(cherrypy.engine, os.path.join(self.base_dir, 'views'))
        cherrypy.engine.jinja2.subscribe()  

        # Database connection management plugin
        from lib.plugin.db import SAEnginePlugin
        cherrypy.engine.db = SAEnginePlugin(cherrypy.engine, app.config['db']['ip'], app.config['db']['port'], app.config['db']['user'], app.config['db']['pswd'], app.config['db']['db'])
        cherrypy.engine.db.subscribe()

        from lib.plugin.scrapper import ScrapperPlugin
        cherrypy.engine.scrapper = ScrapperPlugin(cherrypy.engine)
        cherrypy.engine.scrapper.subscribe()

    def run(self):
        if hasattr(cherrypy.engine, "signal_handler"):
            cherrypy.engine.signal_handler.subscribe()
        if hasattr(cherrypy.engine, "console_control_handler"):
            cherrypy.engine.console_control_handler.subscribe()

        # Start the application
        cherrypy.engine.start()

        # Run the engine main loop
        cherrypy.engine.block()

    def on_error(self, status, message, traceback, version):
        return status

    def make_rotate_logs(self):
        cherrypy.log.error_file = ""
        cherrypy.log.access_file = ""

        # Get config values
        maxBytes = getattr(cherrypy.log, "rot_maxBytes", 10485760)
        backupCount = getattr(cherrypy.log, "rot_backupCount", 5)

        # Make rotating file handler for error log
        fname = getattr(cherrypy.log, "rot_error_file", "./logs/error.log")
        h = handlers.RotatingFileHandler(fname, 'a', maxBytes, backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(_cplogging.logfmt)
        cherrypy.log.error_log.addHandler(h)

        # Make rotating file handler for access log
        fname = getattr(cherrypy.log, "rot_access_file", "./logs/access.log")
        h = handlers.RotatingFileHandler(fname, 'a', maxBytes, backupCount)
        h.setLevel(logging.DEBUG)
        h.setFormatter(_cplogging.logfmt)
        cherrypy.log.access_log.addHandler(h)

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-c", "--conf-file", dest="conf_file", help="Name of the configuration file (defualt: %s)" % default_conf)
    parser.set_defaults(conf_file=default_conf)
    (options, args) = parser.parse_args()
    # Entry point for application
    basedir = os.path.abspath(os.path.curdir)
    print "Starting server in: "+basedir+" with config: "+options.conf_file
    Server(basedir, options.conf_file).run()