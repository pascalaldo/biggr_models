#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
from bigg_models import routes

import asyncio

from tornado import autoreload
from tornado.httpserver import HTTPServer
from tornado.options import define, options, parse_command_line
from tornado.web import Application

# command line options
define("port", default=8888, help="run on given port", type=int)
define("public", default=True, help="run on all addresses")
define("debug", default=False, help="Start server in debug mode")
define("process_i", default=0, help="The index of the process", type=int)

def get_application(debug=False):
    app_routes = routes.get_routes()
    return Application(app_routes, debug=debug)


def start_debug_server():
    import os

    print("Serving BiGG Models on port %d in debug mode" % options.port)
    # This code has some performance issues, so disabled
    autoreload.start()
    for dir, _, files in chain(
        os.walk("bigg_models/templates"),
        # os.walk("bigg_models/static/js"),
        # os.walk("bigg_models/static/css"),
        # os.walk("bigg_models/static/assets"),
    ):
        [autoreload.watch(dir + "/" + f) for f in files if not f.startswith(".")]
    asyncio.run(run_server())


def start_production_server():
    print(
        "Serving BiGG Models on port %d process_nr %d"
        % (options.port, options.process_i)
    )
    asyncio.run(run_server())


async def run_server():
    server = HTTPServer(get_application(debug=options.debug))
    server.listen(options.port, reuse_port=True)
    await asyncio.Event().wait()


def run():
    """Run the server"""
    parse_command_line()

    if options.debug:
        start_debug_server()
    else:
        start_production_server()

if __name__ == "__main__":
    run()
