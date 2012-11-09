#!/usr/bin/python3 -u

import sys
import time
import argparse
from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue, Empty

from Server import Server
from Client import Client
from Testcase import Testcase
from Proxy import Proxy
from Log import *

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def read(queue):
    try:
        return queue.get(timeout=.1) # or q.get_nowait() 
    except Empty:
        pass

def invoke(action):
    agent = agents[action["agent"]]
    agent.actionDone.wait()
    with agent.actionLock:
        agent.action = action
        agent.actionStart.set()
        agent.actionDone.clear()


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Run Polipo test cases')
    argparser.add_argument('testcases', metavar='N', type=int, nargs='+',
                           help='Number of the test case to be run')
    argparser.add_argument('--proxy-port', dest='proxy_port', type=int,
                           default=8124,
                           help='Port of the proxy')
    argparser.add_argument('--proxy-command', dest='proxy_command',
                           default="../polipo",
                           help='Location of polipo')
    argparser.add_argument('--proxy-config', dest='proxy_config',
                           default="polipo.conf",
                           help='Configuration file for Polipo')
    argparser.add_argument('--server-port', dest='server_port', type=int,
                           default=8125,
                           help='Port of the test server')
    argparser.add_argument('--tests-dir', dest='tests_dir',
                           default='data',
                           help='Directory containing test cases')
    argparser.add_argument('--env-dir', dest='env_dir',
                           default='env',
                           help='Directory where temporary files used during the test are stored.')
    argparser.add_argument('--log-file', dest='log_file',
                           default='test.log',
                           help='Log file')
    argparser.add_argument('--selftest', dest='selftest', action='store_true',
                           help='Conduct selftests')
    opts = argparser.parse_args()

    if opts.selftest:
        # When doing selftests, the client connects directly to the
        # server
        opts.proxy_port = opts.server_port
        opts.tests_dir = "selftests"
        
    if len(opts.testcases) != 1:
        print("Currently only one test case can be run.")
        exit(1)

    log_open(opts.log_file)

    testcase_number = opts.testcases[0]

    log(LOG_PROGRESS, None, "Running testcase {}", testcase_number)

    # Parse testcase
    filename = opts.tests_dir + '/' + str(testcase_number)
    with open(filename, "rb") as fh:
        testcase = Testcase(fh.read(), "localhost", opts.server_port)

    if not opts.selftest:
        #Starting Proxy
        proxy = Proxy("proxy",
                      opts.proxy_command,
                      opts.proxy_port,
                      opts.proxy_config,
                      opts.env_dir)
        proxy.start(supplementalConfig=testcase.config)
        proxy.ready.wait(timeout=5)
        if not proxy.poll():
            raise Exception("Failed to start Polipo:\n{}".format("\n".join(proxy.log)))
        else:
            log(LOG_INFO, None, "Proxy started.")

    server = Server("server", opts.server_port)
    server_thread = Thread(target=server.run)
    server_thread.daemon = True
    server_thread.start()
    log(LOG_INFO, None, "server started.")

    client = Client("client", opts.proxy_port)
    client_thread = Thread(target=client.run)
    client_thread.daemon = True
    client_thread.start()
    log(LOG_INFO, None, "client started.")

    agents = { "client": client, "server": server }

    for action in testcase.discourse:
        invoke(action)

    server.actionDone.wait()
    log(LOG_INFO, None, "server finished.")
    client.actionDone.wait()
    log(LOG_INFO, None, "client finished.")
    if not opts.selftest:
        proxy.stop()
    log(LOG_INFO, None, "proxy stopped.")

    log(LOG_PROGRESS, None, "Testcase successfuly completed.")    

