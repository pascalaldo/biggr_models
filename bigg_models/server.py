#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bigg_models import routes

from cobradb.models import *

from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options, parse_command_line
from tornado.web import Application

# command line options
define("port", default=8888, help="run on given port", type=int)
define("public", default=True, help="run on all addresses")
define("debug", default=False, help="Start server in debug mode")
define("processes", default=1, help="number of subprocesses to spawn", type=int)

# -------------------------------------------------------------------------------
# Application API
# -------------------------------------------------------------------------------


def get_application(debug=False):
    app_routes = routes.get_routes()
    return Application(app_routes, debug=debug)


def run():
    """Run the server"""
    parse_command_line()
    server = HTTPServer(get_application(debug=options.debug))
    server.bind(options.port, None if options.public else "localhost")
    if options.debug:
        print("Serving BiGG Models on port %d in debug mode" % options.port)
        if options.processes > 1:
            print("Multiple processes not supported in debug mode")
        server.start()
    else:
        print(
            "Serving BiGG Models on port %d with %d processes"
            % (options.port, options.processes)
        )
        server.start(options.processes)
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        stop()


def stop():
    """Stop the server"""
    IOLoop.current().stop()


# -------------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------------


if __name__ == "__main__":
    run()
