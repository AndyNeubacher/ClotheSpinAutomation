import serial
import time
import threading
import queue
import socket
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging




class GrblStreamer:
    def __init__(self, serial_port:str=None, serial_baud:int=115200, ip_addr=None, ip_port:int=8080, logging=None, loglevel=LogLevel.NONE):
        self.running = False
        self.treads_running = False
        self.read_queue = queue.Queue()
        self.serial: serial.Serial | None = None
        self.socket = None
        self.log = logging
        self.loglevel = loglevel


        if serial_port is not None:
            self.port = serial_port
            self.baudrate = serial_baud

            self.DTR_ENABLE = False
            self.RTS_ENABLE = False
            self.WRITE_TIMEOUT = 1.0

        if ip_addr is not None:
            self.ip_addr = ip_addr
            self.ip_port = ip_port

        self.callback_queue = queue.Queue(100)


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.PrintLog("GrblStreamer", message, msg_level, self.loglevel, Color.CYAN.value)

    def progress_callback(self, percent: int, command: str):
        self._log(f"Progress: {percent}%", LogLevel.DEBUG)
    
    def alarm_callback(self, line: str):
        self._log(f"ALARM detected: {line}", LogLevel.ERROR)
        
    def error_callback(self, line: str):
        self._log(f"ERROR detected: {line}", LogLevel.ERROR)

    def open(self):
        if self.serial is not None:
            self.open_serial()
        elif self.ip_addr is not None:
            self.open_socket()

    #@Logging
    def open_socket(self):
        try:
            self.close_socket()
        except:
            pass

        self._log(f"Connecting to GRBL at {self.ip_addr}:{self.ip_port}", LogLevel.INFO)
        self.socket = socket.socket()
        self.socket.connect((self.ip_addr, self.ip_port))
        self.treads_running = True
        self.read_thread = threading.Thread(target=self._read_loop_socket)
        self.read_thread.daemon = True
        self.read_thread.start()
        
        self.callback_thread = threading.Thread(target=self._callback_loop)
        self.callback_thread.daemon = True
        self.callback_thread.start()

        self._initialize_grbl()


    def open_serial(self):

        try:
            self.close_serial()
        except:
            pass

        try:
            self.serial = serial.Serial()
            self.serial.port = self.port
            self.serial.baudrate = self.baudrate
            self.serial.bytesize = serial.EIGHTBITS
            self.serial.parity = serial.PARITY_NONE
            self.serial.stopbits = serial.STOPBITS_ONE
            self.serial.timeout = None
            self.serial.write_timeout = self.WRITE_TIMEOUT
            self.serial.xonxoff = False
            self.serial.rtscts = False
            self.serial.dsrdtr = False

            self.serial.dtr = self.DTR_ENABLE
            self.serial.rts = self.RTS_ENABLE

            self.serial.open()

            self.serial.reset_output_buffer()
            self.serial.reset_input_buffer()

            self.treads_running = True
            self.read_thread = threading.Thread(target=self._read_loop_serial)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            self.callback_thread = threading.Thread(target=self._callback_loop)
            self.callback_thread.daemon = True
            self.callback_thread.start()

            self._initialize_grbl()

        except serial.SerialException as e:
            if len(self.port) > 4 and self.port[-2:].isdigit():
                try:
                    self.serial.port = self.port[:-1]
                    self.serial.open()
                    self.serial.reset_output_buffer()
                    self.serial.reset_input_buffer()
                except:
                    raise e
            else:
                raise e


    #@Logging
    def _initialize_grbl(self):
        self._log("Initializing GRBL...", LogLevel.INFO)
        if True:
            self.write(b'\x18')  # Ctrl-X
            time.sleep(2)

        if self.serial:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

        self.write_line("$X")
        time.sleep(0.5)


    #@Logging
    def _read_loop_socket(self):
        buffer = ""

        while self.treads_running:
            try:
                if self.socket:
                    char = self.socket.recv(128)
                    if not char:
                        continue
                    buffer += char.decode('utf-8', errors='ignore')
                    if not buffer.endswith('\n'):
                        continue
                    lines = buffer.strip().split('\n')
                    buffer = ""
                    for line in lines:
                        self._process_line(line)

            except Exception as e:
                if self.treads_running:
                    self._log(f"Error in socket-read loop: {e}", LogLevel.ERROR, Color.RED.value)


    def _read_loop_serial(self):
        buffer = ""

        while self.treads_running:
            try:
                if self.serial and self.serial.is_open:
                    char = self.serial.read(1)
                    if not char:
                        continue
                    buffer += char.decode('utf-8', errors='ignore')
                    if not buffer.endswith('\n'):
                        continue
                    line = buffer.strip()
                    buffer = ""
                    if line:
                        self._process_line(line)

            except Exception as e:
                if self.treads_running:
                    print(f"Error in serial-read loop: {e}")
                    

    #@Logging
    def _process_line(self, line):
        self._log(f"Received: {line}", LogLevel.DEBUG)
        if 'ALARM' in line:
            self.write_line("$X")
            try:
                self.callback_queue.put_nowait(('alarm', line))
            except queue.Full:
                pass

        elif 'error' in line.lower():
            try:
                self.callback_queue.put_nowait(('error', line))
            except queue.Full:
                pass

        self.read_queue.put(line)
    

    #@Logging
    def _callback_loop(self):
        while self.treads_running:
            try:
                event_type, data = self.callback_queue.get(timeout=1)
                
                if event_type == 'progress':
                    percent, command = data
                    self.progress_callback(percent, command)
                elif event_type == 'alarm':
                    self.alarm_callback(data)
                elif event_type == 'error':
                    self.error_callback(data)
                    
            except queue.Empty:
                continue
            except:
                pass


    def write(self, data):
        if isinstance(data, str):
            data = data.encode()

        if self.serial and self.serial.is_open:
            self.serial.write(data)
        elif self.socket:
            self.socket.send(data)


    #@Logging
    def write_line(self, text):
        if not text.endswith('\n'):
            text += '\n'
        self._log(f"Sending: {text.strip()}", LogLevel.DEBUG)
        self.write(text)


    def read_line_blocking(self):
        try:
            return self.read_queue.get(timeout=5)
        except queue.Empty:
            return None

    #@Logging
    def send_file(self, file_path: str, completion_timeout: int = 300):

        self.running = True

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

        grbl_buffer = 0
        BUFFER_SIZE = 31#127
        sent_commands = []

        for i, cmd in enumerate(commands, 1):

            while grbl_buffer + len(cmd) + 1 > BUFFER_SIZE - 5:
                response = self.read_line_blocking()
                if response == 'ok' and sent_commands:
                    sent_cmd = sent_commands.pop(0)
                    grbl_buffer -= (len(sent_cmd) + 1)
                elif response and 'error' in response.lower():
                    if sent_commands:
                        sent_cmd = sent_commands.pop(0)
                        grbl_buffer -= (len(sent_cmd) + 1)
    
            self.write_line(cmd)
            sent_commands.append(cmd)
            grbl_buffer += len(cmd) + 1

            if i % 10 == 0:
                percent = int((i / len(commands)) * 100)
                if percent == 100:
                    continue
                try:
                    self.callback_queue.put_nowait(('progress', (percent, cmd)))
                except queue.Full:
                    pass

        start_time = time.time()
        while True:
            if time.time() - start_time > completion_timeout:
                break
                
            self.write_line("?")
            time.sleep(2)
            response = self.read_line_blocking()
            if response and 'Idle' in response:
                break
        
        self._log('Burn completed!', LogLevel.INFO)
        self.progress_callback(100, 'completed')
        self.running = False


    #@Logging
    def close(self):
        self._log("Closing connection", LogLevel.INFO)
        if self.serial:
            self.close_serial()
        
        elif self.socket:
            self.close_socket()


    def close_serial(self):
        self.treads_running = False

        if self.serial and self.serial.is_open:
            try:
                self.serial.reset_output_buffer()
                self.serial.reset_input_buffer()
                self.serial.close()
            except:
                pass

        self.serial = None


    def close_socket(self):
        self.treads_running = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = None


    def Start(self, grbl_file:str=None, timeout_sec=300):
        self.open()

        if grbl_file is not None:
            self.send_file(grbl_file, timeout_sec)


    def WaitForBurnFinished(self):
        while self.running:
            time.sleep(0.5)

        return True


    def Close(self):
        self.close()


if __name__ == "__main__":
    log = Logging(logfile_name='gbrl_streamer_log.txt')
    streamer = GrblStreamer(ip_addr="192.168.1.120", ip_port=8080, logging=log, loglevel=LogLevel.INFO)

    streamer.Start('wer_will_mich.gc', 180)
    streamer.WaitForBurnFinished()