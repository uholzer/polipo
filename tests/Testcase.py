import re

class TestcaseException(Exception):
    def __init__(self, text, testcase=None):
        if testcase.inElement:
            super().__init__("{0} at line {1} in Element {2} starting at line {3}".format(
                text,
                testcase.pos+1 if testcase.pos < len(testcase.lines) else "EOF",
                testcase.inElement[-1],
                testcase.startTagPos[-1]
            ))
        else:
            super().__init__("{0} at line {1}".format(
                text,
                testcase.pos+1
            ))

def elementParser(elementName):
    """Returns a decorator for function which parse a nonempty element:

    It adds a wrapper around the function. It parses the attributes
    and then calls the function with the additional arguments self and
    attributes at the beginning. When the function returns it checks
    whether there is a closing tag and whether it is the right one.
    """
    def decorator(function):
        def wrapper(self, *args, **kwargs):
            tag = self.re_start.match(self.lines[self.pos])
            assert tag and tag.group(1) == elementName
            startpos = self.pos
            self.inElement.append(elementName)
            self.startTagPos.append(startpos)
            attributes = dict() # for future use
            self.pos += 1
            return_value = function(self, attributes, *args, **kwargs)
            end = self.re_end.match(self.lines[self.pos])
            if not end:
                raise TestcaseException("Expected </{}>".format(elementName), 
                                        self.pos, elementName, startpos)
            elif end.group(1) != elementName:
                raise TestcaseException("Wrong closing tag: </{}>".format(end.group(1)), 
                                        self.pos, elementName, startpos)
            self.pos += 1
            self.inElement.pop()
            self.startTagPos.pop()
            return return_value
        return wrapper
    return decorator

class Testcase:
    def __init__(self, description, server_host, server_port):
        self.pos = 0
        self.lines = description.splitlines(True)
        self.inElement = []
        self.startTagPos = []

        # Prepare some regular expressions
        self.re_emptyLine = re.compile(b'^(\s*$|#)')
        self.re_start = re.compile(b'<(\w+)>\s*')
        self.re_end = re.compile(b'^</(\w+)>\s*$')
        self.re_startend = re.compile(b'<(\w+)\s*/>\s*')

        # Values for substitution
        self.server_host = "{}:{}".format(server_host, server_port).encode()
        self.server_url = "http://{}:{}".format(server_host, server_port).encode()

        # Prepare variables
        self.keywords = ""
        self.config = ""
        self.discourse = []

        # Parse
        try:
            self._expect_tag((b'testcase',))
        except IndexError as e:
            if self.pos >= len(self.lines):
                raise TestcaseException("Expected closing tag", self)
            else:
                raise e

    def _skip_empty(self):
        """Skips empty lines and comments"""
        while self.pos < len(self.lines) and self.re_emptyLine.match(self.lines[self.pos]):
            self.pos += 1

    def _expect_tag(self, tagnames, *args, **kwargs):
        """Makes shure that one of tagnames starts at the current line
        and calls the respective parser function.

        If None in tagnames and a closing tag is encountered, this
        function returns instead of raising an Exception."""
        self._skip_empty()
        tag = self.re_start.match(self.lines[self.pos])
        if tag and tag.group(1) in tagnames:
            return_value = getattr(self, "_parse_" + tag.group(1).decode())(*args, **kwargs)
            self._skip_empty()
            return return_value
        elif tag:
            raise TestcaseException("Tag <{}> not allowed".format(tag.group(1)), self)
        elif self.re_end.match(self.lines[self.pos]) and None in tagnames:
            pass
        else:
            raise TestcaseException("Expected a tag", self)
        return None

    @elementParser(b'testcase')
    def _parse_testcase(self, attributes):
        self._expect_tag((b'info',))
        while not self.re_end.match(self.lines[self.pos]):
            self.discourse.extend(self._expect_tag((b'server', b'client')))

    @elementParser(b'info')
    def _parse_info(self, attributes):
        self._expect_tag((b'keywords', b'config', None))
        self._expect_tag((b'keywords', b'config', None))

    @elementParser(b'keywords')
    def _parse_keywords(self, attributes):
        while not self.re_end.match(self.lines[self.pos]):
            self.keywords += self.lines[self.pos].decode()
            self.pos += 1
        
    @elementParser(b'config')
    def _parse_config(self, attributes):
        while not self.re_end.match(self.lines[self.pos]):
            self.config += self.lines[self.pos].decode()
            self.pos += 1

    @elementParser(b'client')
    def _parse_client(self, attributes):
        actions = []
        while not self.re_end.match(self.lines[self.pos]):
            actions.append(self._expect_tag((b'send', b'receive')))
            actions[-1]["agent"] = "client"
        return actions

    @elementParser(b'server')
    def _parse_server(self, attributes):
        actions = []
        while not self.re_end.match(self.lines[self.pos]):
            actions.append(self._expect_tag((b'send', b'receive')))
            actions[-1]["agent"] = "server"
        return actions

    @elementParser(b'send')
    def _parse_send(self, attributes):
        action = {"action": "send", "data": b''}
        while not self.re_end.match(self.lines[self.pos]):
            l = self.lines[self.pos]
            l = self._substitute(l)
            action["data"] += l
            self.pos += 1
        return action

    @elementParser(b'receive')
    def _parse_receive(self, attributes):
        action = {"action": "receive", "data": b''}
        while not self.re_end.match(self.lines[self.pos]):
            l = self.lines[self.pos]
            l = self._substitute(l)
            action["data"] += l
            self.pos += 1
        return action

    def _substitute(self, data):
        data = data.replace(b'%SERVER_URL', self.server_url)
        data = data.replace(b'%SERVER_HOST', self.server_host)
        return data

