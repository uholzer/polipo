#!/usr/bin/python3 -u

import sys
import socketserver
import threading

from Agent import Agent
from Log import *

class Server(Agent):
    def __init__(self, name, port):
        self.name = name
        self.server = _TCPServer(("localhost", port), None)
        self.socket = None
        self.clientAddress = None
        self.actionStart = threading.Event()
        self.actionDone = threading.Event()
        self.actionDone.set()
        self.actionLock = threading.Lock()

    def verify_request(self, request, client_address):
        log(LOG_DEBUG, self, "client_address is", client_address)

    def run(self):
        while True:
            self.actionStart.wait()
            self.actionLock.acquire()
            self.actionStart.clear()
            log(LOG_DEBUG, self, "Server got action {}.", self.action)
            if self.action["action"] == "send":
                if self.socket is not None:
                    self.send(self.socket, self.action["data"])
                else:
                    log(LOG_INFO, self, "Not connected to a client, can't send")
            elif self.action["action"] == "receive":
                (self.socket, self.clientAddress) = self.server.get_request()
                log(LOG_DEBUG, self, "Got request from {}", self.clientAddress)
                self.receive(self.socket, self.action)
            else:
                raise Exception("Unsupported action")
            self.actionDone.set()
            self.actionLock.release()

class _TCPServer(socketserver.TCPServer):
    pass

class ServerHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per socket to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        pass
