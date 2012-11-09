#!/usr/bin/python3 -u

import sys
import socket
import threading

from Agent import Agent
from Log import *

class Client(Agent):
    def __init__(self, name, remote_port):
        self.name = name
        self.remote_port = remote_port
        self.action = None
        self.actionStart = threading.Event()
        self.actionDone = threading.Event()
        self.actionDone.set()
        self.actionLock = threading.Lock()
        self.socket = None

    def run(self):
        while True:
            self.actionStart.wait()
            self.actionLock.acquire()
            self.actionStart.clear()
            log(LOG_DEBUG, self, "Client got action {}", self.action)
            if self.action["action"] == "send":
                if not self.socket:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect(("localhost", self.remote_port))
                self.send(self.socket, self.action["data"])
            elif self.action["action"] == "receive":
                if self.socket:
                    self.receive(self.socket, self.action)
                else:
                    log(LOG_INFO, self, "Not connected to a server, can't receive")
            else:
                raise Exception("Unsupported action")
            self.actionDone.set()
            self.actionLock.release()



