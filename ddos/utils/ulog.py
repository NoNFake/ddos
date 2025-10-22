import logging
from .ucolor import (
    red, blue, yellow, black, white,
    bold, reset, bg_red
)


class ColoredFormater(logging.Formatter):
    def __init__(self):
        super().__init__()

        self.usr_name = 'SYSTEM'


    def set_username(self, usr_name: str):
        self.usr_name = usr_name


    def get_lvlname(self, record):
        return f"[{record.levelname:^8}] [{record.name}] [{self.usr_name}]"

    FORMATS = {
        logging.DEBUG:     lambda self, record: f"{white}{bold}{self.get_lvlname(record)} {blue}>>{white} {record.getMessage()} {reset}",
        logging.INFO:      lambda self, record: f"{black}{bold}{self.get_lvlname(record)} {blue}>>{white} {record.getMessage()} {reset}",
        logging.WARNING:   lambda self, record: f"{yellow}{bold}{self.get_lvlname(record)} {blue}>>{white} {record.getMessage()} {reset}",
        logging.ERROR:     lambda self, record: f"{red}{bold}{self.get_lvlname(record)} {blue}>>{white} {record.getMessage()} {reset}",
        logging.CRITICAL:  lambda self, record: f"{bg_red}{bold}{self.get_lvlname(record)} {blue}>>{white} {record.getMessage()} {reset}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        return log_fmt(self, record)



# logging.basicConfig(
#     level=logging.INFO,
#     format=f"{bold}{cyan}[%(asctime)s] {black}= %(levelname)s = {blue}>> {white}%(message)s",
#     datefmt="%H:%M:%S",

# )

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormater())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],)

global log
# LOGGER 
log = logging.getLogger(__name__)
log.critical("Logging system: log.info... / log_on / log_off")
# log  = lambda args : logger.info(args)

def log_off(): log = logging.disable()
def log_on(): log = logging.disable(logging.NOTSET)
