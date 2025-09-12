import serial
import time
import threading
import queue
import socket
from ping3 import ping
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging




class GrblStreamer:
    def __init__(self, ip_addr=None, ip_port:int=8080, logging=None, loglevel=LogLevel.NONE):
        self.log = logging
        self.loglevel = loglevel
        self.ip_addr = ip_addr
        self.ip_port = ip_port

        self.socket = self._open_socket()
        self.connected = self.IsLaserConnected()
        self._init_laser()


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.PrintLog("GrblStreamer", message, msg_level, self.loglevel, color)


    def _open_socket(self):
        try:
            self._log(f"opening tcp-socket to {self.ip_addr}:{self.ip_port}", LogLevel.DEBUG)
            sock = socket.socket()
            sock.settimeout(1)
            sock.connect((self.ip_addr, self.ip_port))
            return sock
        
        except:
            self._log(f"failed to open a GRBL socket to {self.ip_addr}:{self.ip_port}", LogLevel.ERROR)
            return None


    def _query_line_retry(self, data, timeout=10, num_retries=3):
        if self.socket is None:
            return None, None

        for attempt in range(num_retries):
            status, lines = self._query_line(data, timeout)
            if status == 'ok' or status == 'alarm':
                return status, lines
            else:
                self._log(f"Error on attempt {attempt + 1} of {num_retries} for command: {data.strip()}, answer {lines}", LogLevel.ERROR)
                self.socket.close()
                self.socket = self._open_socket()

            time.sleep(0.1)  # Wait before retrying

        self._log(f"Failed to get 'ok' after {num_retries} retries for command: {data.strip()}", LogLevel.ERROR)
        return None, None


    def _query_line(self, data, timeout=10):
            if self.socket is None:
                return None, None

            if not data.endswith('\n'):
                data += '\n'
            self._log(f"Sending : {data.strip()}", LogLevel.DEBUG)

            if isinstance(data, str):
                data = data.encode()

            buffer = ""
            lines = []
            self.socket.settimeout(timeout)
            try:
                self.socket.sendall(data)
                while True:
                    char = self.socket.recv(1024)
                    if not char:
                        continue
                    buffer += char.decode('utf-8', errors='ignore')
                    if not buffer.endswith('\n'):
                        continue

                    lines = buffer.splitlines()
                    for line in lines:
                        if lines and 'ok' in lines[-1]:
                            self._log(f'Received: {lines}', LogLevel.DEBUG)
                            return 'ok', lines
                        elif 'alarm' in line.lower():
                            self._log(f'Received ALARM: {buffer.strip()}', LogLevel.ERROR)
                            return 'alarm', lines
                        elif 'error' in line.lower():
                            self._log(f'Received ERROR: {buffer.strip()}', LogLevel.ERROR)
                            return 'error', lines


            except socket.timeout:
                self._log("Server timed out waiting for data from the client. Connection closing.", LogLevel.ERROR)
                return 'timeout', None
            except Exception as e:
                self._log(f"An error occurred: {e}", LogLevel.ERROR)
                return 'exception', e


    def _init_laser(self):
        if self.socket is None:
            return

        self._log("Init Laser", LogLevel.INFO)
        self.socket.send(bytes([0x18]))             # softreset
        version = self._query_line_retry('$I', 1)   # get grbl-version
        offsets = self._query_line_retry('$#', 1)   # get grbl-offsets
        self._query_line_retry('$H', 15)            # bring laser in home position


    def _send_file(self, file_path:str, timeout:int = 300):
        job_start_time = time.time()

        self._log(f"Sending file: {file_path}", LogLevel.INFO)
        with open(file_path, 'r') as f:
            lines = f.readlines()

        commands = []
        for line in lines:
            line = line.strip()
            if ';' in line:
                line = line[:line.index(';')]
            if '(' in line:
                line = line[:line.index('(')]
            line = line.strip()
            
            if line:
                commands.append(line)        

        percent = 0
        sent_commands = []
        PROGRESS_UPDATE_SEC = 10

        progress_update = time.time()
        for i, cmd in enumerate(commands, 1):

            if (time.time() - progress_update) > PROGRESS_UPDATE_SEC:
                progress_update = time.time()
                self._log(f'Burn progress {percent}%', LogLevel.INFO)

            if time.time() - job_start_time > timeout:
                self._log(f'Burn job-timeout after {timeout}sec!', LogLevel.ERROR)
                return False

            sent_commands.append(cmd)
            status, rx_lines = self._query_line_retry(cmd, 20)
            if status is None:
                return False        # timeout or exception occoured!
            elif 'error' in status or 'alarm' in status or 'timeout' in status or 'exception' in status:
                return False

            if i % 10 == 0:
                percent = int((i / len(commands)) * 100)
                if percent == 100:
                    continue

            if ((time.time() - progress_update) % PROGRESS_UPDATE_SEC) == 0:
                progress_update = time.time()
                self._log(f'Burn progress {percent}%', LogLevel.INFO)


        # now wait to finish the job
        isRunning = True
        while isRunning:
            time.sleep(0.5)
            if time.time() - job_start_time > timeout:
                self._log(f'Burn completion-timeout after {timeout}sec!', LogLevel.ERROR)
                return False
                
            status, rx_lines = self._query_line_retry("?")
            if status is None:
                self._log(f'Burn completion-error after {timeout}sec!', LogLevel.ERROR)
                return False
            elif 'ok' in status and 'Idle' in rx_lines[0]:
                isRunning = False


        min, sec = divmod(time.time() - job_start_time, 60)
        self._log(f'Burn completed in {int(min):02}:{int(sec):02}sec', LogLevel.INFO)
        return True


    def Close(self):
        self.connected = False
        self._log("Closing connection", LogLevel.INFO)
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = None


    def Start(self, grbl_file:str=None, timeout_sec=300):
        if not self.connected or grbl_file is None:
            return False

        res = self._send_file(grbl_file, timeout_sec)
        if res is False:
            self.Stop()

        return res


    def Stop(self):
        self._log("Stopping Laser", LogLevel.INFO)
        self._query_line_retry('$X')  # reset laser
        self._query_line_retry('$H')  # re-home


    def IsLaserConnected(self):
        if self.socket is None:
            return False

        response_time = ping(self.ip_addr, unit='s', timeout=1)
        if response_time is not None and response_time is not False:
            res = self._query_line_retry('G0')
            if res is not None and 'ok' in res:
                return True

        return False






if __name__ == "__main__":
    log = Logging(logfile_name='gbrl_streamer_log.txt')
    streamer = GrblStreamer(ip_addr="192.168.1.120", logging=log, loglevel=LogLevel.INFO)

    streamer.Start('low_light_test_fast.gc', 180)
    #streamer.Start('lightburn_gcode.txt', 180)
    #streamer.Start('low_light_test.gc', 180)
    streamer.Close()