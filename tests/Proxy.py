from subprocess import Popen, PIPE
import threading
import os
from Log import *

class Proxy:
    def __init__(self, name, command, port, configFile, envdir):
        self.name = name
        self.command = command
        self.port = port
        self.configFile = configFile
        self.envdir = envdir
        self.finalConfigFile = envdir + "/polipo.conf"
        self.supplementalConfig = ""
        self.thread = threading.Thread(target=self._run)
        self.process = None
        self.ready = threading.Event()

        # Create directories and clean up existing path
        if not os.path.exists(envdir):
            os.mkdir(envdir)
        if not os.path.exists(envdir + "/cache"):
            os.mkdir(envdir + "/cache")
        else:
            for root, dirs, files in os.walk(envdir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            

    def start(self, supplementalConfig=""):
        basic = open(self.configFile, 'r')
        final = open(self.finalConfigFile, 'w')
        for l in iter(basic.readline, ""): final.write(l)
        final.write("\n")
        final.write("proxyPort = {}\n".format(self.port))
        final.write("diskCacheRoot = {}\n".format(os.path.abspath(self.envdir + "/cache")))
        final.write(supplementalConfig)
        self.supplementalConfig = supplementalConfig
        self.thread.start()

    def stop(self):
        try:
            self.process.terminate()
        except:
            pass
        self.process.wait()
        self.thread.join()
        self.ready.clear()

    def poll(self):
        return True if self.process else False

    def _run(self):
        self.process = Popen((self.command, "-c", self.finalConfigFile),
                             stderr=PIPE, universal_newlines=True)
        
        for l in iter(self.process.stderr.readline, ""):
            log(LOG_INFO, self, l)
            if (l.find("Established") >= 0):
                self.ready.set()
        self.process = None

