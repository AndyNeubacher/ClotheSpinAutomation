import socket
import time
import subprocess
import tkinter as tk
from tkinter import filedialog
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging



class LightBurn:
    def __init__(self, app_path, ip_address, logging=None, loglevel=LogLevel.NONE, timeout=3):
        self.ip_address = ip_address
        self.port_in = 19841
        self.port_out = 19840
        self.sock_in = None
        self.sock_out = None
        self.timeout = timeout
        self.log = logging
        self.loglevel = loglevel

        self._start_application(app_path)
        time.sleep(3)  # Wait for LightBurn to start
        
        self._open_socket()
        self.connected = self._check_connection()


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.Print("LightBurn", message, msg_level, self.loglevel, Color.BLUE.value)


    @Logging()
    def _start_application(self, path):
        self._log("Start application", LogLevel.INFO)
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0
        subprocess.Popen(path, startupinfo=info)    # This will start LightBurn, unfortunately in the foreground.


    @Logging()
    def _open_socket(self):
        try:
            self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._log(f"Socket opened successfully for {self.ip_address}, in={self.port_in}, out={self.port_out}", LogLevel.INFO)
            return True
        except socket.error as e:
            self._log(f"Error opening socket: {e}", LogLevel.ERROR)
            self.sock_out = None
            return False


    @Logging()
    def _sendcmd(self, command):
        if self.sock_out is None:
            self._log("Socket is not open. Cannot send command.", LogLevel.ERROR)
            return False

        if isinstance(command, str):
            command_data = command.encode('utf-8')
        elif isinstance(command, bytes):
            command_data = command
        else:
            self._log("Invalid command type. Must be string or bytes.", LogLevel.ERROR)
            return False

        try:
            self._log(f"Sending command '{command}' sent to {self.ip_address}:{self.port_out}", LogLevel.DEBUG)
            self.sock_out.sendto(command_data, (self.ip_address, self.port_out))
            return True
        except socket.error as e:
            self._log(f"Error sending command: {e}", LogLevel.ERROR)
            return False


    @Logging()
    def _close_socket(self):
        if self.sock_out:
            self.sock_out.close()
            self._log(f"Socket closed for {self.ip_address}:{self.port_out}", LogLevel.INFO)
            self.sock_out = None
            self.connected = False


    @Logging()
    def _check_connection(self):
        if self.sock_out:
            self._sendcmd("PING")
            try:
                self.sock_in.bind(('', self.port_in))
                self.sock_in.settimeout(self.timeout)
                data, addr = self.sock_in.recvfrom(1024)
                self._log(f"Received response from {addr}: {data.decode('utf-8')}", LogLevel.INFO)

                if data == b'OK':
                    self._log(f"Connection established!", LogLevel.INFO)
                    return True
                else:
                    self._log("No Connection!", LogLevel.ERROR)
                    return False
            except socket.timeout:
                self._log("No response received within timeout period.", LogLevel.ERROR)
                return False
            except socket.error as e:
                self._log(f"Error receiving data: {e}", LogLevel.ERROR)
                return False


    @Logging()
    def _get_status(self):
        if not self.connected:
            self._log("Not connected. Cannot get status.", LogLevel.ERROR)
            return None

        self._sendcmd("STATUS")
        try:
            data, addr = self.sock_in.recvfrom(1024)
            return data.decode('utf-8')
        except socket.timeout:
            self._log("No response received within timeout period.", LogLevel.ERROR)
            return None
    

    @Logging()
    def IsIdle(self):
        status = self._get_status()
        self._log(f"IsIdle: {status}", LogLevel.DEBUG)
        if status and "OK" in status:
            return True
        return False


    @Logging()
    def WaitForBurnFinished(self, startup_sec=1, timeout_sec=60):
        self._log("Waiting for burn to finish...", LogLevel.INFO)
        t_start = time.time()
        while (True):
            res = self.IsIdle()

            # ignore the first x seconds
            if time.time() - t_start < startup_sec:
                continue

            if res:
                self._log("Burn finished!", LogLevel.INFO)
                return True

            if time.time() - t_start > timeout_sec:
                self._log("Burn timed out!", LogLevel.ERROR)
                return False
            
            self._log("Burn still in progress...", LogLevel.DEBUG)
            time.sleep(1)


    @Logging()
    def LoadFile(self, filename):
        if not self.connected:
            self._log("Not connected. Cannot load file.", LogLevel.ERROR)
            return False
        self._log(f"Loading file: {filename}", LogLevel.INFO)
        self._sendcmd(f'LOADFILE:' + filename)


    @Logging()
    def Start(self):
        self._log("Starting burn...", LogLevel.INFO)
        self._sendcmd("START")


    @Logging()
    def Close(self):
        self._close_socket()


    @Logging()
    def SelectAndLoadLightBurnFile(self, dir=".", filename=None):
        try:
            root = tk.Tk()
            root.withdraw()

            if filename is None:
                file_path = filedialog.askopenfilename(
                    initialdir=dir,
                    title="Select a File",
                    filetypes=[("LightBurn files", "*.lbrn2")]
                )
                root.destroy()
                if not file_path:
                    self._log("No file selected.", LogLevel.ERROR)
                    return False
            
                self.LoadFile(file_path)
            else:
                self.LoadFile(dir + "\\" + filename)
            return True
        
        except Exception as e:
            self._log(f"Error selecting LightBurn file: {e}", LogLevel.ERROR)
            return False