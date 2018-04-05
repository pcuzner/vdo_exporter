#!/usr/bin/env python2

import signal
import socket
import threading
import time
import logging
import logging.handlers
import argparse
import sys

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from vdo_exporter import VDOStats
from vdo_exporter.utils import valid_ipv4, valid_tcp_port


class Handler(BaseHTTPRequestHandler):
    """ HHTP request handler for this prometheus exporter endpoint """
    quiet = False
    valid_routes = ['/', '/metrics']

    def log_message(self, format_str, *args):
        """ write a log message for all successful requests """
        if Handler.quiet:
            pass
        else:
            # default way of handling successful requests
            msg_template = format_str.replace('%s', '{}')

            sys.stderr.write("{} - - [{}] {}\n".format(
                                                  self.address_string(),
                                                  self.log_date_time_string(),
                                                  msg_template.format(*args)))

    def root(self):
        """ webserver root, just shows a link to /metrics endpoint """

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.wfile.write("""
          <!DOCTYPE html>
          <html>
            <head><title>VDO Prometheus Exporter</title></head>
            <body>
              <h1>VDO Prometheus Exporter</h1>
              <p><a href='/metrics'>Metrics</a></p>
            </body>
          </html>""")

    def metrics(self):
        """
        Create a VDOstats object, collect vdo device information, format
        it and return to the caller in text/plain format
        """

        stats = VDOStats()
        stats.collect()

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(stats.formatted())
        self.wfile.write('\n')

    def do_GET(self):
        """ GET request handler, just handle '/' or '/metrics' endpoints """

        if self.path not in Handler.valid_routes:
            self.send_error(404, message="Undefined endpoint")
            return

        if self.path == '/':
            self.root()
        elif self.path == '/metrics':
            self.metrics()


class PrometheusExporter(ThreadingMixIn, HTTPServer):
    """Basic multi-threaded HTTP server"""
    stop = False


def shutdown(*args):
    """ Shutdown the program. Called by a SIGTERM interrupt """

    logger.info("Exporter received shutdown request")
    exporter.stop = True
    exporter.shutdown()


def get_opts():
    """ Process invocation options """

    parser = argparse.ArgumentParser(description="VDO Statistics Prometheus "
                                                 "Exporter")

    parser.add_argument('--debug', action="store_true",
                        default=False)
    parser.add_argument('--port', type=valid_tcp_port,
                        default=9286)
    parser.add_argument('--ip', type=valid_ipv4,
                        default='0.0.0.0')
    parser.add_argument('--quiet', action="store_true",
                        default=False)

    return parser.parse_args()


def main():
    """ Main loop """

    logger.info("Starting exporter")
    exporter_thread = threading.Thread(target=exporter.serve_forever)
    exporter_thread.daemon = True

    logger.debug("HTTP server thread is {}".format(exporter_thread.name))
    exporter_thread.start()
    logger.info("Exporter listening on http://{}:{}".format(opts.ip,
                                                            opts.port))

    # To allow the http server to shutdown cleanly we need to run it is a
    # separate daemon thread, which means the main thread just needs to sit
    # and wait until we update the http server's 'stop' attribute
    while not exporter.stop:
        time.sleep(0.5)


if __name__ == "__main__":

    opts = get_opts()
    logger = logging.getLogger(name="vdo_exporter")

    if opts.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    lh = logging.handlers.SysLogHandler(address='/dev/log')
    logger.addHandler(lh)

    signal.signal(signal.SIGTERM, shutdown)

    Handler.quiet = opts.quiet

    try:
        exporter = PrometheusExporter((opts.ip, opts.port), Handler)
    except socket.error:
        logger.critical("Port {} already in use - unable to start (use "
                        "--port to avoid conflicts)".format(opts.port))
        sys.exit(1)
    else:
        logger.debug("Exporter bind to {}:{} successful".format(opts.ip,
                                                                opts.port))

    main()
