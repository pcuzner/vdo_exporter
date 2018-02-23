#!/usr/bin/env python2

import signal

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
from vdo_exporter import VDOStats


DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 9285


class Handler(BaseHTTPRequestHandler):
    valid_routes = ['/', '/metrics']

    def root(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.wfile.write("""
          <!DOCTYPE html>
          <html>
            <head><title>VDO POC Exporter</title></head>
            <body>
              <h1>VDO POC Prometheus Exporter</h1>
              <p><a href='/metrics'>Metrics</a></p>
            </body>
          </html>""")

        pass

    def metrics(self):

        stats = VDOStats()
        stats.collect()

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(stats.formatted())
        self.wfile.write('\n')

    def do_GET(self):

        if self.path not in Handler.valid_routes:
            self.send_error(404, message="Undefined endpoint")
            return

        if self.path == '/':
            self.root()
        elif self.path == '/metrics':
            self.metrics()


class PromExporter(ThreadingMixIn, HTTPServer):
    """Simple multi-threaded http instance"""


def start_exporter():

    try:
        exporter.serve_forever()
    except KeyboardInterrupt:
        pass

    shutdown()


def shutdown():
    exporter.server_close()


def main():
    start_exporter()


if __name__ == "__main__":

    signal.signal(signal.SIGTERM, shutdown)

    exporter = PromExporter((DEFAULT_IP, DEFAULT_PORT), Handler)

    main()
