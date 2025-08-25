import json
import requests
from lxml import html
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging



class Tasmota:
    def __init__(self, ipv4, logging=None, loglevel=LogLevel.NONE, timeout=3):
        self.ipv4 = ipv4
        self.url = f'http://{self.ipv4}/'
        self.stream_open = False
        self.timeout = timeout
        self.connected = self.check_connection()
        self.log = logging
        self.loglevel = loglevel


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.Print("Tasmota", message, msg_level, self.loglevel, Color.GREEN.value)


    def _get_from_xpath(self, x):
        r = requests.get(self.url + '', timeout=self.timeout)
        tree = html.fromstring(r.content)
        c = tree.xpath(f'{x}/text()')
        return c


    @Logging()
    def check_connection(self):
        if self.get_name() is None:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return False
        self._log(f"Tasmota: Connected to device '{self.get_name()}'", LogLevel.INFO)
        return True


    @Logging()
    def get_name(self):
        try:
            text = self._get_from_xpath('/html/body/div/div[1]/h3')[0]
            self._log(f"Tasmota: Device name is '{text}'", LogLevel.DEBUG)
            return str(text)
        except requests.RequestException:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return None


    @Logging()
    def check_output(self, number):
        if not self.connected:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return "Tasmota: Device not connected"
        r = requests.get(self.url + f'cm?cmnd=Power{number}%20', timeout=self.timeout)
        self._log(f"Tasmota: Output {number} is {r.content}", LogLevel.DEBUG)
        return r.content


    @Logging()
    def SetOutput(self, number, state):
        if not self.connected:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return "Tasmota: Device not connected"
        r = requests.get(self.url + f'cm?cmnd=Power{number}%20{state}', timeout=self.timeout)
        self._log(f"Tasmota: Set output {number} to {state}, response: {r.content}", LogLevel.INFO)
        return r.content


    @Logging()
    def get_stream_url(self):
        if not self.connected:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return "Tasmota: Device not connected"
        if not self.stream_open:
            r = requests.get(self.url, timeout=self.timeout)
            self.stream_open = True
        return f'http://{self.ipv4}:81/stream'


    @Logging()
    def get_power_monitoring_attribute(self, attribute):
        """
        possible attributes are:
        Total, Yesterday, Today, Power, ApparentPower, ReactivePower, Factor, Voltage, Current
        """
        if not self.connected:
            self._log("Tasmota: Device not connected", LogLevel.ERROR)
            return "Tasmota: Device not connected"
        else:
            if 'Monitoring' in self.get_name():
                r = requests.get(self.url + f'cm?cmnd=Status%208', timeout=self.timeout)
                text = str(r.content)
                j = json.loads(text[2:-1])
                self._log(f"Tasmota: Power monitoring attribute '{attribute}' is {j['StatusSNS']['ENERGY'][attribute]}", LogLevel.DEBUG)
                return j['StatusSNS']['ENERGY'][attribute]
            else:
                self._log('Tasmota: power monitoring not supported for this device', LogLevel.ERROR)
                return None
