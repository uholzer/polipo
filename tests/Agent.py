import socket
from Log import *

class Agent:

    def receive(self, s, discourse):
        # Read all headers
        data = b''
        header_end = -1
        log(LOG_INFO, self, "receiving:\n--------*--------")
        while (header_end < 0):
            received = s.recv(1024)
            log(LOG_INFO, self, received)
            data += received
            header_end = data.find(b'\r\n\r\n')

        body_start = header_end + 4

        content_length = 0
        if ("expected-content-length" in discourse):
            content_length = discourse["expected-content-length"]
        else:
            # Look for a Content-length header
            cl_index = data.find(b'\r\nContent-length: ', 0, header_end)
            if (cl_index >= 0):
                cl_end_index += 18
                assert(cl_end_index >= cl_index)
                try:
                    content_length = int(data[cl_index, cl_end_index])
                except (ValueError):
                    # We have an invalid content-length header!
                    content_length = 0
            else:
                # Content length is missing entirely. Assume no body.
                content_length = 0
        
        body_end = body_start
        while (body_end < body_start + content_length):
            received = s.recv(1024)
            log(LOG_INFO, self, received)
            data += received
            body_end = len(data)

        self.action["received"] = data

        log(LOG_INFO, self, "--------*--------")
        

    def send(self, s, data):
        log(LOG_INFO, self, "sending ...")
        log(LOG_DEBUG, self, data)
        log(LOG_INFO, self, "done sending.")
        s.sendall(data)


