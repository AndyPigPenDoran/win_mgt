
import logging
import getpass

class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = '\x1b[38;20m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self):
        self.fmt = "[%(levelname)s] %(message)s"
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.grey + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    

def get_password(user, password):
    """Prompt for password - when no cred id is used or an override is requested"""

    if password is not None and len(password) > 0:
        # Use this password
        return password

    return getpass.getpass("Provide the password for %s: " % user)

def pad_string(to_pad, pad_len, pad_char=" ", truncate=False):
    """Pad a string to a given size"""
    to_pad_len = len(to_pad)

    if to_pad_len >= pad_len:
        if truncate:
            return to_pad[:pad_len]
        else:
            return to_pad
    return "%s%s"% (to_pad, pad_char * (pad_len - to_pad_len))
        
def show_inputs(logger, args):
    """For debug, show the inputs"""
    _msg = "Input arguments:\n\n"
    _pad_len = 30
    
    for arg in vars(args):
        if arg == "pwd":
            _msg += "  %s: **********\n" % pad_string(arg, _pad_len)
        else:
            _msg += "  %s: %s\n" % (pad_string(arg, _pad_len), getattr(args, arg))

    logger.debug(_msg)

