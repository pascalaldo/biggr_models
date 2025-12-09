#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
from bigg_models import routes

import asyncio

import tornado
from tornado import autoreload
from tornado.netutil import bind_sockets
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


def start_debug_server():
    import os

    server = HTTPServer(get_application(debug=options.debug))
    server.bind(options.port, None if options.public else "localhost")

    print("Serving BiGG Models on port %d in debug mode" % options.port)
    if options.processes > 1:
        print("Multiple processes not supported in debug mode")
    autoreload.start()
    for dir, _, files in chain(
        os.walk("bigg_models/templates"),
        os.walk("bigg_models/static/js"),
        os.walk("bigg_models/static/css"),
        os.walk("bigg_models/static/assets"),
    ):
        [autoreload.watch(dir + "/" + f) for f in files if not f.startswith(".")]
    server.start(1)


def start_production_server():
    print(
        "Serving BiGG Models on port %d with %d processes"
        % (options.port, options.processes)
    )
    sockets = bind_sockets(options.port)
    tornado.process.fork_processes(options.processes)

    async def post_fork_main():
        server = HTTPServer(get_application(debug=options.debug))
        server.add_sockets(sockets)
        await asyncio.Event().wait()

    asyncio.run(post_fork_main())


def run():
    """Run the server"""
    parse_command_line()

    if options.debug:
        start_debug_server()
    else:
        start_production_server()


# -------------------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------------------


if __name__ == "__main__":
    run()
