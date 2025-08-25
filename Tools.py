import logging
from enum import Enum
from datetime import datetime


class LogLevel(Enum):
    NONE = 0
    ERROR = 1
    INFO = 2
    DEBUG = 3

class Color(Enum):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37


g_intent = None


class Logging:
    def __init__(self, logfile_name='logfile.txt', loglevel=LogLevel.INFO):
        if logging.getLogger().hasHandlers():
            logging.getLogger().handlers.clear()

        logging.basicConfig(filename=logfile_name, level=logging.ERROR)
        logging.error("----- New Log Session -----")
        self.loglevel = loglevel
        global g_intent
        if g_intent is None:
            g_intent = 0


    def __call__(self, func):
        def wrapper(*args, **kwargs):
            global g_intent
            self_instance = args[0]
            g_intent += 3
            try:
                # Call the original function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                self_instance.Print(f"Exception in {func.__name__}: {str(e)}", LogLevel.ERROR, Color.RED.value)
                raise e
            finally:
                g_intent -= 3
        return wrapper


    def SetColor(self, text="", color_code=Color.WHITE.value):
        return f"\033[{color_code}m{text}\033[0m"


    def Print(self, device="", message="", msg_level=None, class_level=None, color=None):
        global g_intent
        if msg_level is None:
            msg_level = class_level

        nest = ' ' * g_intent

        now = datetime.now()
        ts = now.strftime("%H:%M:%S") + ":" + f"{int(now.microsecond/1000):03d}"

        if class_level.value >= msg_level.value:
            if msg_level == LogLevel.ERROR:
                print(self.SetColor(f"{ts} {device} ERROR: {nest}{message}", color if color is not None else Color.RED.value))
                logging.error(f"{ts} {device} ERROR: {nest}{message}")
            elif msg_level == LogLevel.INFO:
                print(self.SetColor(f"{ts} {device} INFO : {nest}{message}", color if color is not None else Color.WHITE.value))
                logging.info(f"{ts} {device} INFO : {nest}{message}")
            elif msg_level == LogLevel.DEBUG:
                print(self.SetColor(f"{ts} {device} DEBUG: {nest}{message}", color if color is not None else Color.YELLOW.value))
                logging.debug(f"{ts} {device} DEBUG: {nest}{message}")
            else:
                print(self.SetColor(f"{ts} {device} UNKNOWN: {nest}{message}", color if color is not None else Color.MAGENTA.value))
                logging.warning(f"{ts} {device} UNKNOWN: {nest}{message}")


