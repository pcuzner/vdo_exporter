#!/usr/bin/env python2

import argparse
import socket


def valid_tcp_port(port_num):
    """ Check port number is valid """

    port_invalid_msg = ("Port number ({}) must be an integer "
                        "(1024-65536)".format(port_num))
    try:
        port = int(port_num)
    except:
        raise argparse.ArgumentTypeError(port_invalid_msg)
    else:
        if 1023 < port <= 65536:
            return port
        else:
            raise argparse.ArgumentTypeError(port_invalid_msg)


def valid_ipv4(ip_string):
    """ Check that the given ip address string is a valid ipv4 address """

    try:
        socket.inet_aton(ip_string)
    except socket.error:
        raise argparse.ArgumentTypeError("Invalid IP address - must be ipv4")
    else:
        return ip_string
