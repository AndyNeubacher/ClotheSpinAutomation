import requests
import json
import time
import sys
import threading
import msvcrt
import select

class RoArmM2S:
    def __init__(self, ip_address, timeout=10):
        self.ip_address = ip_address
        self.base_url = f"http://{self.ip_address}/js"
        self.timeout = timeout
        print(f"RoArm-M2-S initialized with IP: {self.ip_address}")


    def _send_command(self, command_data):
        try:
            json_str = json.dumps(command_data)
            url = f"{self.base_url}?json={json_str}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            if response.status_code != 200:
                print(f"RoArm-M2-S: HTTP request failed with status {response.status_code}")
                return None
            json_answer = response.json()
            if json_answer is None:
                return True
            return json_answer
        except requests.exceptions.Timeout:
            print(f"RoArm-M2-S: Request timed out after {self.timeout} seconds.")
            return None
        except requests.exceptions.ConnectionError:
            print(f"RoArm-M2-S: Could not connect to RoArm-M2-S at {self.ip_address}. "
                  "Please check power, network connection, and IP address.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"RoArm-M2-S: HTTP request failed with status {e.response.status_code}: {e.response.text}")
            return None
        except json.JSONDecodeError:
            print(f"RoArm-M2-S: Could not decode JSON response: {response.text}")
            return None
        except Exception as e:
            print(f"RoArm-M2-S: An unexpected error occurred: {e}")
            return None


    def InitPosition(self):
        command = {"T": 100}
        response = self._send_command(command)
        return self.GetPosition()


    def GetPosition(self):
        command = {"T": 105}
        return self._send_command(command)


    def GetPositionReadable(self):
        pos = self.GetPosition()
        if pos is None:
            return "Could not retrieve position."

        b_rad = pos.get('b', 0)
        s_rad = pos.get('s', 0)
        e_rad = pos.get('e', 0)
        t_rad = pos.get('t', 0)

        b_deg = round(b_rad * 180 / 3.141592653589793, 2)
        s_deg = round(s_rad * 180 / 3.141592653589793, 2)
        e_deg = round(e_rad * 180 / 3.141592653589793, 2)
        t_deg = 180 - round(t_rad * 180 / 3.141592653589793, 2)

        x = pos.get('x', 0)
        y = pos.get('y', 0)
        z = pos.get('z', 0)

        return (f"X: {x:.2f} mm, Y: {y:.2f} mm, Z: {z:.2f} mm\n"
            f"Base: {b_deg:.2f}°, Shoulder: {s_deg:.2f}°, Elbow: {e_deg:.2f}°, Tool: {t_deg:.2f}°")


    def TeachMode(self):
        self.SetTorqueLock(False)
        loop = True
        while loop:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\x1b', b'q', b'Q'):  # ESC or 'q'
                    print("RoArm-M2-S: Exiting teach mode.")
                    loop = False
            time.sleep(0.05)
            print(self.GetPositionReadable())
        self.SetTorqueLock(True)


    def SetTorqueLock(self, enable: bool):
        cmd_value = 1 if enable else 0
        command = {"T": 210, "cmd": cmd_value}
        return self._send_command(command)


    def SetDynamicForceAdaption(self, enable: bool, base: int, shoulder: int, elbow: int, hand: int):
        on_off = 1 if enable else 0
        command = {"T": 112, "mode":on_off, "b":base,"s":shoulder,"e":elbow,"h":hand}
        return self._send_command(command)


    def SetJointPID(self, joint: int, p: int = 16, i: int = 0):
        #BASE_JOINT = 1, SHOULDER_JOINT = 2, ELBOW_JOINT = 3, EOAT_JOINT = 4
        #p: default 16, i: default 0 (multiples of 8)
        command = {"T": 108, "joint": joint, "p": p, "i": i}
        return self._send_command(command)


    def SetLed(self, enable: bool):
        led_value = 255 if enable else 0
        command = {"T": 114, "led": led_value}
        response = self._send_command(command)
        return response is not None


    def MoveToXYZ(self, x=None, y=None, z=None, tool=None, speed=500):
        tool = (180-tool) * 3.141592653589793 / 180.0
        command = {"T":104, "x":x, "y":y, "z":z, "t":tool, "spd":speed}
        if x is not None:
            command["x"] = round(x, 4)
        if y is not None:
            command["y"] = round(y, 4)
        if z is not None:
            command["z"] = round(z, 4)

        return self._send_command(command)


    def SetGripper(self, angle_deg: int):
        #BASE_JOINT = 1, SHOULDER_JOINT = 2, ELBOW_JOINT = 3, EOAT_JOINT = 4
        #p: default 16, i: default 0 (multiples of 8)
        angle_rad = (180-angle_deg) * 3.141592653589793 / 180.0
        command = {"T": 103, "axis": 4, "pos": round(angle_rad, 4), "spd": 0.25}
        return self._send_command(command)











    def move_to_joint_angles(self, base=None, shoulder=None, elbow=None, hand=None, speed=500):
        """
        Moves the robotic arm to specified joint angles (in radians).

        Args:
            base (float, optional): Base joint angle in radians (-3.14 to 3.14).
            shoulder (float, optional): Shoulder joint angle in radians (-1.57 to 1.57).
            elbow (float, optional): Elbow joint angle in radians (-1.11 to 3.14).
            hand (float, optional): Hand/gripper joint angle in radians (clamp: 1.08 to 3.14, wrist: 1.08 to 5.20).
            speed (int, optional): Movement speed in steps/second (0 for max speed).
                                   One full rotation is 4096 steps.
        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        command = {"T": 102, "spd": speed} # CMD_JOINTS_RAD_CTRL
        if base is not None:
            command["b"] = round(base, 4)
        if shoulder is not None:
            command["s"] = round(shoulder, 4)
        if elbow is not None:
            command["e"] = round(elbow, 4)
        if hand is not None:
            command["h"] = round(hand, 4)

        response = self._send_command(command)
        return response is not None








    # You can add more specific control functions based on the Waveshare JSON commands:
    # (Refer to "RoArm-M2-S JSON Command Meaning" on Waveshare Wiki)

    # Example: Single joint control
    def control_single_joint(self, joint_id: int, angle: float, speed: int = 500):
        """
        Controls a single joint to a specified angle.

        Args:
            joint_id (int): 0 for Base, 1 for Shoulder, 2 for Elbow, 3 for Hand.
            angle (float): Target angle in radians.
            speed (int, optional): Movement speed.
        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        command = {"T": 101, "id": joint_id, "rad": round(angle, 4), "spd": speed} # CMD_SINGLE_JOINT_CTRL
        response = self._send_command(command)
        return response is not None


