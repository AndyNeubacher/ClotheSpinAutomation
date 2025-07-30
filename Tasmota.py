import json
import requests
from lxml import html


class Tasmota:
    def __init__(self, ipv4, timeout=3):
        self.ipv4 = ipv4
        self.url = f'http://{self.ipv4}/'
        self.stream_open = False
        self.timeout = timeout
        self.connected = self.check_connection()


    def _get_from_xpath(self, x):
        r = requests.get(self.url + '', timeout=self.timeout)
        tree = html.fromstring(r.content)
        c = tree.xpath(f'{x}/text()')
        return c


    def check_connection(self):
        if self.get_name() is None:
            return False
        return True


    def get_name(self):
        try:
            text = self._get_from_xpath('/html/body/div/div[1]/h3')[0]
            return str(text)
        except requests.RequestException:
            print("Tasmota: Device not connected")
            return None


    def check_output(self, number):
        if not self.connected:
            return "Tasmota: Device not connected"
        r = requests.get(self.url + f'cm?cmnd=Power{number}%20', timeout=self.timeout)
        return r.content


    def set_output(self, number, state):
        if not self.connected:
            return "Tasmota: Device not connected"
        r = requests.get(self.url + f'cm?cmnd=Power{number}%20{state}', timeout=self.timeout)
        return r.content


    def get_stream_url(self):
        if not self.connected:
            return "Tasmota: Device not connected"
        if not self.stream_open:
            r = requests.get(self.url, timeout=self.timeout)
            self.stream_open = True
        return f'http://{self.ipv4}:81/stream'


    def get_power_monitoring_attribute(self, attribute):
        """
        possible attributes are:
        Total, Yesterday, Today, Power, ApparentPower, ReactivePower, Factor, Voltage, Current
        """
        if not self.connected:
            return "Tasmota: Device not connected"
        else:
            if 'Monitoring' in self.get_name():
                r = requests.get(self.url + f'cm?cmnd=Status%208', timeout=self.timeout)
                text = str(r.content)
                j = json.loads(text[2:-1])
                return j['StatusSNS']['ENERGY'][attribute]
            else:
                print('Tasmota: power monitoring not supported for this device')
                return None
