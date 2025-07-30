import socket
import time
import subprocess
import tkinter as tk
from tkinter import filedialog


class LightBurn:
    def __init__(self, app_path, ip_address, timeout=3):
        self.ip_address = ip_address
        self.port_in = 19841
        self.port_out = 19840
        self.sock_in = None
        self.sock_out = None
        self.timeout = timeout

        self._start_application(app_path)
        time.sleep(3)  # Wait for LightBurn to start
        
        self._open_socket()
        self.connected = self._check_connection()


    def _start_application(self, path):
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0
        print("LightBurn: starting application")
        subprocess.Popen(path, startupinfo=info)    # This will start LightBurn, unfortunately in the foreground.


    def _open_socket(self):
        try:
            self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"LightBurn: Socket opened successfully for {self.ip_address}, in={self.port_in}, out={self.port_out}")
            return True
        except socket.error as e:
            print(f"LightBurn: Error opening socket: {e}")
            self.sock_out = None
            return False


    def _sendcmd(self, command):
        """
        Sends a UDP packet with the given command to the specified IP address and port.

        Args:
            command (str or bytes): The command to send. If a string, it will be encoded to UTF-8.

        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        if self.sock_out is None:
            print("LightBurn: Socket is not open. Cannot send command.")
            return False

        if isinstance(command, str):
            command_data = command.encode('utf-8')
        elif isinstance(command, bytes):
            command_data = command
        else:
            print("LightBurn: Invalid command type. Must be string or bytes.")
            return False

        try:
            self.sock_out.sendto(command_data, (self.ip_address, self.port_out))
            print(f"LightBurn: Command '{command}' sent to {self.ip_address}:{self.port_out}")
            return True
        except socket.error as e:
            print(f"LightBurn: Error sending command: {e}")
            return False


    def _close_socket(self):
        """
        Closes the UDP socket.
        """
        if self.sock_out:
            self.sock_out.close()
            print(f"LightBurn: Socket closed for {self.ip_address}:{self.port_out}")
            self.sock_out = None
            self.connected = False


    def _check_connection(self):
        if self.sock_out:
            self._sendcmd("PING")
            try:
                self.sock_in.bind(('', self.port_in))
                self.sock_in.settimeout(self.timeout)
                data, addr = self.sock_in.recvfrom(1024)
                print(f"LightBurn: Received response from {addr}: {data.decode('utf-8')}")

                if data == b'OK':
                    print(f"LightBurn: Connection established!")
                    return True
                else:
                    print("LightBurn: No Connection!")
                    return False
            except socket.timeout:
                print("LightBurn: No response received within timeout period.")
                return False
            except socket.error as e:
                print(f"LightBurn: Error receiving data: {e}")
                return False


    def _get_status(self):
        """
        Sends a status request command to the laser and returns the response.

        Returns:
            str: The status response from the laser.
        """
        if not self.connected:
            print("LightBurn: Not connected. Cannot get status.")
            return None

        self._sendcmd("STATUS")
        try:
            data, addr = self.sock_in.recvfrom(1024)
            return data.decode('utf-8')
        except socket.timeout:
            print("LightBurn: No response received within timeout period.")
            return None
    

    def IsIdle(self):
        status = self._get_status()
        if status and "OK" in status:
            return True
        return False


    def WaitForBurnFinished(self, timeout):
        start_time = time.time()
        while (self.IsIdle() == False):
            if time.time() - start_time > timeout:
                print("Burn timed out!")
                return False
            time.sleep(1)
        return True             # Burn finished successfully


    def LoadFile(self, filename):
        self._sendcmd(f'LOADFILE:' + filename)


    def Start(self):
        self._sendcmd("START")


    def Close(self):
        self._close_socket()


    def SelectAndLoadLightBurnFile(self, initial_dir="."):
        try:
            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(
                initialdir=initial_dir,
                title="Select a File",
                filetypes=[("LightBurn files", "*.lbrn2")]
            )
            root.destroy()
            if not file_path:
                print("No file selected.")
                return False
            
            self.LoadFile(file_path)
            return True
        
        except Exception as e:
            print(f"Error selecting LightBurn file: {e}")
            return False






    