import threading

LOG_PROGRESS = 0
LOG_INFO = 1
LOG_DEBUG = 2

log_file = None
log_file_level = LOG_DEBUG
log_stdout_level = LOG_INFO

lock = threading.Lock()

def log_open(filename=None):
    global log_file
    log_file = open(filename, "w")

def log_format(agent, template, *args):
    if isinstance(template, bytes): template = template.decode()
    for i, arg in enumerate(args):
        if isinstance(arg, bytes):
            args[i] = arg.decode()
    if (args):
        message = template.format(*args)
    else:
        message = template
    if agent:
        message = "".join(["{}: {}".format(agent.name, l) for l in message.splitlines(True)])
    return message

def log(level, agent, template, *args):
    with lock:
        message = log_format(agent, template, *args)
        if (level <= log_stdout_level): print(message)
        if (level <= log_file_level): print(message, file=log_file)

__all__ = [ "log", "log_open", "LOG_PROGRESS", "LOG_INFO", "LOG_DEBUG" ]

