import requests
import json
import time
import msvcrt
import math
import time
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging
from ping3 import ping




class Joint(Enum):
    BASE = 1
    SHOULDER = 2
    ELBOW = 3
    TOOL = 4





class RoArmM2S:
    def __init__(self, ip_address, logging=None, loglevel=LogLevel.NONE, timeout=3):
        self.ip_address = ip_address
        self.base_url = f"http://{self.ip_address}/js"
        self.timeout = timeout
        self.log = logging
        self.loglevel = loglevel
        self.connected = False

        ret = self.InitPosition()
        if ret is None:
            self._log("Initialization failed.", LogLevel.ERROR)
        else:
            self._log(f"initialized with IP: {self.ip_address}", LogLevel.INFO)


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.Print("RoArm-M2-S", message, msg_level, self.loglevel, color)


    @Logging()
    def _send_command(self, command_data):
        try:
            self.connected = False
            json_str = json.dumps(command_data)
            url = f"{self.base_url}?json={json_str}"
            self._log(f"_send_command: {url}", LogLevel.DEBUG)
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            if response.status_code != 200:
                self._log(f"HTTP request failed with status {response.status_code}", LogLevel.ERROR)
                return None
            
            self.connected = True
            json_answer = response.json()
            self._log(f"Response: {json_answer}", LogLevel.DEBUG, Color.GREEN.value)
            if json_answer is None:
                return True
            return json_answer
        except requests.exceptions.Timeout:
            self._log(f"Request timed out after {self.timeout} seconds.", LogLevel.ERROR)
            return None
        except requests.exceptions.ConnectionError:
            self._log(f"Could not connect to RoArm-M2-S at {self.ip_address}. "
                  "Please check power, network connection, and IP address.", LogLevel.ERROR)
            return None
        except requests.exceptions.HTTPError as e:
            self._log(f"HTTP request failed with status {e.response.status_code}: {e.response.text}", LogLevel.ERROR)
            return None
        except json.JSONDecodeError:
            self._log(f"Could not decode JSON response: {response.text}", LogLevel.ERROR)
            return None
        except Exception as e:
            self._log(f"An unexpected error occurred: {e}", LogLevel.ERROR)
            return None
                

    @Logging()
    def InitPosition(self):
        self._log("InitPosition: Initializing robot arm.", LogLevel.INFO)
        # check if the robot arm is reachable
        if self._wait_for_reboot_finished(self.ip_address, 1) == False:
            self.connected = False
            self._log(f"Could not connect to RoArm-M2-S at {self.ip_address}.", LogLevel.ERROR)
            return None
        
        # reboot ESP32
        #command = {"T": 600}
        #response = self._send_command(command)
        #if self._wait_for_reboot_finished(self.ip_address, 20) == False:
        #    print(f"Reboot failed or timed out.")
        #    return None

        # turn on LED during initialization
        self.SetLed(True)

        # reset old PID settings
        command = {"T": 109}
        response = self._send_command(command)

        self.SetTorqueLock(True)
        self.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)

        # move arm in to avoid collision
        self.MoveSingleJoint(Joint.SHOULDER.value, angle=10, speed=20, acc=5, tolerance=10, timeout=2)
        self.MoveSingleJoint(Joint.ELBOW.value, angle=150, speed=20, acc=5, tolerance=10, timeout=2)

        # init arm-position
        command = {"T": 100}
        response = self._send_command(command)
        
        # move arm in to avoid collision
        self.MoveSingleJoint(Joint.ELBOW.value, 150, speed=100, acc=10, tolerance=10, timeout=3)

        self.SetLed(False)

        self._log(self.GetPositionReadable(), LogLevel.INFO)
        return self.GetPosition()



    @Logging()
    def GetPosition(self):
        self._log("GetPosition: Retrieving current position.", LogLevel.DEBUG)
        command = {"T": 105}
        return self._send_command(command)



    @Logging()
    def GetAngle(self, joint_id):
        if(joint_id < 1 or joint_id > 4):
            self._log(f"Invalid joint ID {joint_id}. Must be between 1 and 4.", LogLevel.ERROR)
            return None

        position_data = self.GetPosition()
        if position_data is None:
            return None

        if joint_id == Joint.BASE.value:
            angle_rad = position_data.get('b', None)
        elif joint_id == Joint.SHOULDER.value:
            angle_rad = position_data.get('s', None)
        elif joint_id == Joint.ELBOW.value:
            angle_rad = position_data.get('e', None)
        elif joint_id == Joint.TOOL.value:
            angle_rad = position_data.get('t', None)

        res = angle_rad * 180 / math.pi
        self._log(f"GetAngle: joint_id={joint_id}, angle={round(res,2)}°", LogLevel.DEBUG)
        return res


    @Logging()
    def GetTorque(self, joint_id):
        if(joint_id < 1 or joint_id > 4):
            self._log(f"RoArm-M2-S: Invalid joint ID {joint_id}. Must be between 1 and 4.", LogLevel.ERROR)
            return None

        position_data = self.GetPosition()
        if position_data is None:
            self._log(f"RoArm-M2-S: Could not retrieve position data for torque.", LogLevel.ERROR)
            return None

        if joint_id == Joint.BASE.value:
            torque = position_data.get('torB', None)
        elif joint_id == Joint.SHOULDER.value:
            torque = position_data.get('torS', None)
        elif joint_id == Joint.ELBOW.value:
            torque = position_data.get('torE', None)
        elif joint_id == Joint.TOOL.value:
            torque = position_data.get('torH', None)

        self._log(f"GetTorque: joint_id={joint_id}, torque={torque}", LogLevel.DEBUG)
        return torque



    @Logging()
    def GetPositionReadable(self):
        pos = self.GetPosition()
        if pos is None:
            self._log(f"RoArm-M2-S: Could not retrieve position data.", LogLevel.ERROR)
            return None

        b_rad = pos.get('b', 0)
        s_rad = pos.get('s', 0)
        e_rad = pos.get('e', 0)
        t_rad = pos.get('t', 0)

        b_deg = round(b_rad * 180 / math.pi, 2)
        s_deg = round(s_rad * 180 / math.pi, 2)
        e_deg = round(e_rad * 180 / math.pi, 2)
        t_deg = 180 - round(t_rad * 180 / math.pi, 2)

        x = pos.get('x', 0)
        y = pos.get('y', 0)
        z = pos.get('z', 0)

        t_b = pos.get('torB', 0)
        t_s = pos.get('torS', 0)
        t_e = pos.get('torE', 0)
        t_t = pos.get('torH', 0)

        self._log(f"GetPositionReadable: X={x}, Y={y}, Z={z}, b={b_deg}°, s={s_deg}°, e={e_deg}°, t={t_deg}°, torque B/S/E/T={t_b}/{t_s}/{t_e}/{t_t}", LogLevel.DEBUG)
        return (f"X:{x:.2f}, Y:{y:.2f}, Z:{z:.2f}, b:{b_deg:.2f}, s:{s_deg:.2f}, e:{e_deg:.2f}, t:{t_deg:.2f}, torque:{t_b:.0f}/{t_s:.0f}/{t_e:.0f}/{t_t:.0f}")



    @Logging()
    def TeachMode(self):
        self.SetTorqueLock(False)
        loop = True
        while loop:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\x1b', b'q', b'Q'):  # ESC or 'q'
                    self._log("RoArm-M2-S: Exiting teach mode.", LogLevel.INFO)
                    loop = False
            time.sleep(0.05)
            print(self.GetPositionReadable())
        self.SetTorqueLock(True)



    @Logging()
    def SetTorqueLock(self, enable: bool):
        self._log(f"SetTorqueLock: {'Enabling' if enable else 'Disabling'} torque lock.", LogLevel.INFO)
        cmd_value = 1 if enable else 0
        command = {"T": 210, "cmd": cmd_value}
        ret = self._send_command(command)
        return ret


    @Logging()
    def SetDynamicForceAdaption(self, enable: bool, base: int, shoulder: int, elbow: int, hand: int):
        self._log(f"SetDynamicForceAdaption: {'Enabling' if enable else 'Disabling'} with base={base}, shoulder={shoulder}, elbow={elbow}, hand={hand}", LogLevel.INFO)
        on_off = 1 if enable else 0
        command = {"T": 112, "mode":on_off, "b":base,"s":shoulder,"e":elbow,"h":hand}
        ret = self._send_command(command)
        return ret


    @Logging()
    def SetJointPID(self, joint: int, p: int = 16, i: int = 0):
        #BASE_JOINT = 1, SHOULDER_JOINT = 2, ELBOW_JOINT = 3, EOAT_JOINT = 4
        #p: default 16, i: default 0 (multiples of 8)
        self._log(f"SetJointPID: joint={joint}, p={p}, i={i}", LogLevel.INFO)
        command = {"T": 108, "joint": joint, "p": p, "i": i}
        ret = self._send_command(command)
        return ret


    @Logging()
    def SetLed(self, enable: bool):
        self._log(f"SetLed: {'Turning ON' if enable else 'Turning OFF'} LED.", LogLevel.INFO)
        led_value = 255 if enable else 0
        command = {"T": 114, "led": led_value}
        response = self._send_command(command)
        return response is not None



    @Logging()
    def SetGripper(self, angle_deg: float, speed=5):
        self._log(f"SetGripper: Moving gripper to {angle_deg}° at speed {speed}.", LogLevel.INFO)
        self.MoveSingleJoint(Joint.TOOL.value, angle_deg, speed=speed, acc=5, tolerance=5, timeout=3)



    @Logging()
    def MoveToXYZT(self, x=None, y=None, z=None, tool=None, speed=5, tolerance=5, timeout=10):
        tool = tool * math.pi / 180.0
        cmd = {"T":104}
        cmd["x"] = round(x, 4)
        cmd["y"] = round(y, 4)
        cmd["z"] = round(z, 4)
        cmd["t"] = round(tool, 4)
        cmd["spd"] = round(speed, 4)

        self._log(f"MoveToXYZT: Moving to X={cmd['x']}, Y={cmd['y']}, Z={cmd['z']}, T={cmd['t']}, Speed={cmd['spd']}", LogLevel.INFO)

        if x is None or y is None or z is None:
            self._log("MoveToXYZT: At least one of x, y, or z is not specified!", LogLevel.ERROR)
            return False

        if self._send_command(cmd) is None:
            return False

        start_time = time.time()
        while True:
            # check for given timeout
            if time.time() - start_time > timeout:
                self._log("MoveToXYZT: timeout reached while waiting for X/Y/Z/T position", LogLevel.ERROR)
                self._log(self.GetPositionReadable(), LogLevel.ERROR)
                return False

            position_data = self.GetPosition()
            if position_data is None:
                self._log("Failed to get position. Retrying...", LogLevel.ERROR)
                return False

            x_current = round(position_data.get('x', None), 2)
            y_current = round(position_data.get('y', None), 2)
            z_current = round(position_data.get('z', None), 2)

            if x is not None and (x_current is None or abs(x_current - x) > tolerance):
                self._log(f"X not within tolerance: current={x_current}, target={x}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            if y is not None and (y_current is None or abs(y_current - y) > tolerance):
                self._log(f"Y not within tolerance: current={y_current}, target={y}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            if z is not None and (z_current is None or abs(z_current - z) > tolerance):
                self._log(f"Z not within tolerance: current={z_current}, target={z}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            break

        self._log(f"MoveToXYZT:   +-> Reached target position X={x_current}, Y={y_current}, Z={z_current}", LogLevel.INFO)
        return True



    @Logging()
    def MoveSingleJoint(self, joint_id: int, angle: float, speed=5, acc=10, tolerance=5, timeout=3):
        self._log(f"MoveSingleJoint: id={joint_id}, angle={angle}, speed={speed}, acc={acc}", LogLevel.INFO)
        command = {"T":121,"joint":joint_id,"angle":angle,"spd":speed,"acc":acc}
        if self._send_command(command) is None:
            return False
        
        start_time = time.time()
        while True:
            #pos = self.GetPosition()
            # check for given timeout
            if time.time() - start_time > timeout:
                self._log("MoveSingleJoint: timeout reached while waiting for joint movement", LogLevel.ERROR)
                self._log(self.GetPositionReadable(), LogLevel.ERROR)
                return False

            act_angle = round(self.GetAngle(joint_id), 2)
            if act_angle is None:
                self._log("Failed to get position. Retrying...", LogLevel.ERROR)
                return False

            if abs(act_angle - angle) > tolerance:  # Check if within 1 degree tolerance
                continue
            
            break

        self._log(f"MoveSingleJoint:   --> id={joint_id} reached target angle {angle}° (current: {act_angle}°)", LogLevel.INFO)
        return True


    @Logging()
    def MoveSingleJointTorqueLimited(self, joint_id: int, angle: float, speed=5, acc=10, max_torque=5, timeout=3):
        command = {"T":121,"joint":joint_id,"angle":angle,"spd":speed,"acc":acc}
        self._log(f"MoveSingleJointTorqueLimited: id={joint_id}, angle={angle}, speed={speed}, acc={acc}", LogLevel.INFO)
        if self._send_command(command) is None:
            return False
        
        start_time = time.time()
        while True:
            # check for given timeout
            if time.time() - start_time > timeout:
                self._log("MoveSingleJointTorqueLimited: timeout reached while waiting for joint movement", LogLevel.ERROR)
                self._log(self.GetPositionReadable(), LogLevel.ERROR)
                return False

            act_torque = self.GetTorque(joint_id)
            if max_torque > 0:
                if act_torque < max_torque:
                    continue
            else:
                if act_torque > max_torque:
                    continue
            break

        self._log(f"MoveSingleJointTorqueLimited:   --> id={joint_id} reached target torque {act_torque}", LogLevel.INFO)
        return True


    @Logging()
    def MoveAllJoints(self, base=None, shoulder=None, elbow=None, tool=None, speed=5, tolerance=5, timeout=3):
        self._log(f"MoveAllJoints: base={base}, shoulder={shoulder}, elbow={elbow}, tool={tool}, speed={speed}", LogLevel.INFO)
        command = {"T":122,"b":base,"s":shoulder,"e":elbow,"h":tool,"spd":speed,"acc":10}
        if base is not None:
            command["b"] = round(base, 4)
        if shoulder is not None:
            command["s"] = round(shoulder, 4)
        if elbow is not None:
            command["e"] = round(elbow, 4)
        if tool is not None:
            command["h"] = round(tool, 4)

        if self._send_command(command) is None:
            return False
        
        start_time = time.time()
        while True:
            # check for given timeout
            if time.time() - start_time > timeout:
                self._log("MoveAllJoints: Timeout reached while waiting for angle-setting", LogLevel.ERROR)
                self._log(self.GetPositionReadable(), LogLevel.ERROR)
                return False

            position_data = self.GetPosition()
            if position_data is None:
                self._log("Failed to get position. Retrying...", LogLevel.ERROR)
                return False

            a_base     = round(position_data.get('b', None) * 180 / math.pi, 2)
            a_shoulder = round(position_data.get('s', None) * 180 / math.pi, 2)
            a_elbow    = round(position_data.get('e', None) * 180 / math.pi, 2)
            a_tool     = round(position_data.get('t', None) * 180 / math.pi, 2)


            if a_base is not None and (a_base is None or abs(a_base - base) > tolerance):
                self._log(f"BASE not within tolerance: current={a_base}, target={base}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            if a_shoulder is not None and (a_shoulder is None or abs(a_shoulder - shoulder) > tolerance):
                self._log(f"SHOULDER not within tolerance: current={a_shoulder}, target={shoulder}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            if a_elbow is not None and (a_elbow is None or abs(a_elbow - elbow) > tolerance):
                self._log(f"ELBOW not within tolerance: current={a_elbow}, target={elbow}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            if a_tool is not None and (a_tool is None or abs(a_tool - tool) > tolerance):
                self._log(f"TOOL not within tolerance: current={a_tool}, target={tool}", LogLevel.DEBUG)
                time.sleep(0.1)
                continue

            break

        self._log(f"MoveAllJoints:   --> reached target angles!", LogLevel.INFO)
        return True



    @Logging()
    def _wait_for_reboot_finished(self, target_ip: str, timeout_seconds: int) -> bool:
        self._log(f"Waiting for RoArm-M2-S at {target_ip} to become reachable...", LogLevel.INFO)
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            response_time = ping(target_ip, unit='s', timeout=1)
            if response_time is not None and response_time is not False:
                self._log(f"RoArm-M2-S at {target_ip} is reachable (ping time: {response_time:.2f} s).", LogLevel.INFO)
                return True
            else:
                time.sleep(1)

        self._log(f"Timeout reached: RoArm-M2-S at {target_ip} is not reachable after {timeout_seconds} seconds.", LogLevel.ERROR)
        return False