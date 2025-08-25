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
    def __init__(self, logfile_name=None, loglevel=LogLevel.INFO):
        self.loglevel = loglevel
        global g_intent
        if g_intent is None:
            g_intent = 0
        if logfile_name is not None:
            self.fd = open(logfile_name, 'w+')


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
                if self.fd is not None:
                    self.fd.write(f"{ts} {device} ERROR: {nest}{message}\n")

            elif msg_level == LogLevel.INFO:
                print(self.SetColor(f"{ts} {device} INFO : {nest}{message}", color if color is not None else Color.WHITE.value))
                if self.fd is not None:
                    self.fd.write(f"{ts} {device} INFO : {nest}{message}\n")

            elif msg_level == LogLevel.DEBUG:
                print(self.SetColor(f"{ts} {device} DEBUG: {nest}{message}", color if color is not None else Color.YELLOW.value))
                if self.fd is not None:
                    self.fd.write(f"{ts} {device} DEBUG: {nest}{message}\n")

            else:
                print(self.SetColor(f"{ts} {device} UNKNOWN: {nest}{message}", color if color is not None else Color.MAGENTA.value))
                if self.fd is not None:
                    self.fd.write(f"{ts} {device} UNKNOWN: {nest}{message}\n")


    def Close(self):
        if self.fd is not None:
            self.fd.close()