import requests
import json
import time
import msvcrt
import math
from enum import Enum
import time
from ping3 import ping




class Joint(Enum):
    BASE = 1
    SHOULDER = 2
    ELBOW = 3
    TOOL = 4





class RoArmM2S:
    def __init__(self, ip_address, timeout=10):
        self.ip_address = ip_address
        self.base_url = f"http://{self.ip_address}/js"
        self.timeout = timeout
        print(f"RoArm-M2-S initialized with IP: {self.ip_address}")
        self.InitPosition()



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
        # check if the robot arm is reachable
        if self._wait_for_reboot_finished(self.ip_address, 1) == False:
            print(f"RoArm-M2-S: Could not connect to RoArm-M2-S at {self.ip_address}.")
            return None
        
        # reboot ESP32
        #command = {"T": 600}
        #response = self._send_command(command)
        #if self._wait_for_reboot_finished(self.ip_address, 20) == False:
        #    print(f"RoArm-M2-S: Reboot failed or timed out.")
        #    return None

        self.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)

        # reset old PID settings
        command = {"T": 109}
        response = self._send_command(command)

        # init arm-position
        command = {"T": 100}
        response = self._send_command(command)
        
        #self.MoveToXYZT(100, 100, -20, 0, 0.3, 10, 3)
        print(self.GetPositionReadable())
        return self.GetPosition()



    def GetPosition(self):
        command = {"T": 105}
        return self._send_command(command)



    def GetAngle(self, joint_id):
        if(joint_id < 1 or joint_id > 4):
            print(f"RoArm-M2-S: Invalid joint ID {joint_id}. Must be between 1 and 4.")
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

        return angle_rad * 180 / math.pi



    def GetTorque(self, joint_id):
        if(joint_id < 1 or joint_id > 4):
            print(f"RoArm-M2-S: Invalid joint ID {joint_id}. Must be between 1 and 4.")
            return None

        position_data = self.GetPosition()
        if position_data is None:
            return None

        if joint_id == Joint.BASE.value:
            torque = position_data.get('torB', None)
        elif joint_id == Joint.SHOULDER.value:
            torque = position_data.get('torS', None)
        elif joint_id == Joint.ELBOW.value:
            torque = position_data.get('torE', None)
        elif joint_id == Joint.TOOL.value:
            torque = position_data.get('torH', None)

        return torque



    def GetPositionReadable(self):
        pos = self.GetPosition()
        if pos is None:
            return "Could not retrieve position."

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

        return (f"X:{x:.2f}, Y:{y:.2f}, Z:{z:.2f}, b:{b_deg:.2f}, s:{s_deg:.2f}, e:{e_deg:.2f}, t:{t_deg:.2f}, torque:{t_b:.0f}/{t_s:.0f}/{t_e:.0f}/{t_t:.0f}")



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



    def SetGripper(self, angle_deg: float, speed=0.2):
        self.MoveSingleJoint(Joint.TOOL.value, angle_deg, speed=speed, acc=5, tolerance=5, timeout=3)



    def MoveToXYZT(self, x=None, y=None, z=None, tool=None, speed=0.1, tolerance=5, timeout=10):
        tool = tool * math.pi / 180.0
        command = {"T":104, "x":x, "y":y, "z":z, "t":tool, "spd":speed}
        if x is not None:
            command["x"] = round(x, 4)
        if y is not None:
            command["y"] = round(y, 4)
        if z is not None:
            command["z"] = round(z, 4)

        print(f"MoveToXYZ: Moving to X={x}, Y={y}, Z={z}, Tool={tool}, Speed={speed}")
        if self._send_command(command) is None:
            return False

        start_time = time.time()
        while True:
            # check for given timeout
            if time.time() - start_time > timeout:
                print("MoveToXYZ: timeout reached while waiting for X/Y/Z position")
                print(self.GetPositionReadable())
                return False

            position_data = self.GetPosition()
            if position_data is None:
                print("Failed to get position. Retrying...")
                return False

            x_current = position_data.get('x', None)
            y_current = position_data.get('y', None)
            z_current = position_data.get('z', None)

            if x is not None and (x_current is None or abs(x_current - x) > tolerance):
                #print(f"X not within tolerance: current={x_current}, target={x}")
                time.sleep(0.1)
                continue

            if y is not None and (y_current is None or abs(y_current - y) > tolerance):
                #print(f"Y not within tolerance: current={y_current}, target={y}")
                time.sleep(0.1)
                continue

            if z is not None and (z_current is None or abs(z_current - z) > tolerance):
                #print(f"Z not within tolerance: current={z_current}, target={z}")
                time.sleep(0.1)
                continue

            break

        #print(f"MoveToXYZ:   +-> Reached target position X={x_current}, Y={y_current}, Z={z_current}")
        # All coordinates are within tolerance
        return True



    def MoveSingleJoint(self, joint_id: int, angle: float, speed=0.2, acc=10, tolerance=5, timeout=3):
        command = {"T":121,"joint":joint_id,"angle":angle,"spd":speed,"acc":acc}
        #print(f"MoveSingleJoint: id={joint_id}, angle={angle}, speed={speed}, acc={acc}")
        if self._send_command(command) is None:
            return False
        
        start_time = time.time()
        while True:
            #pos = self.GetPosition()
            # check for given timeout
            if time.time() - start_time > timeout:
                print("MoveToXYZ: timeout reached while waiting for joint movement")
                print(self.GetPositionReadable())
                return False

            act_angle = self.GetAngle(joint_id)
            if act_angle is None:
                print("Failed to get position. Retrying...")
                return False

            if abs(act_angle - angle) > tolerance:  # Check if within 1 degree tolerance
                continue
            
            break

        #print(f"MoveSingleJoint:   +-> id={joint_id} reached target angle {angle}° (current: {act_angle}°)")
        return True


    def MoveSingleJointTorqueLimited(self, joint_id: int, angle: float, speed=0.2, acc=10, max_torque=5, timeout=3):
        command = {"T":121,"joint":joint_id,"angle":angle,"spd":speed,"acc":acc}
        print(f"MoveSingleJoint: id={joint_id}, angle={angle}, speed={speed}, acc={acc}")
        if self._send_command(command) is None:
            return False
        
        start_time = time.time()
        while True:
            # check for given timeout
            if time.time() - start_time > timeout:
                print("MoveToXYZ: timeout reached while waiting for joint movement")
                print(self.GetPositionReadable())
                return False

            act_torque = self.GetTorque(joint_id)
            print(act_torque)
            if max_torque > 0:
                if act_torque < max_torque:
                    continue
            else:
                if act_torque > max_torque:
                    continue
            break

        return True


    def MoveAllJoints(self, base=None, shoulder=None, elbow=None, tool=None, speed=0.2, tolerance=5, timeout=3):
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
                print("MoveToXYZ: Timeout reached while waiting for angle-setting")
                print(self.GetPositionReadable())
                return False

            position_data = self.GetPosition()
            if position_data is None:
                print("Failed to get position. Retrying...")
                return False

            a_base     = position_data.get('b', None) * 180 / math.pi
            a_shoulder = position_data.get('s', None) * 180 / math.pi
            a_elbow    = position_data.get('e', None) * 180 / math.pi
            a_tool     = position_data.get('t', None) * 180 / math.pi


            if a_base is not None and (a_base is None or abs(a_base - base) > tolerance):
                #print(f"BASE not within tolerance: current={a_base}, target={base}")
                time.sleep(0.1)
                continue

            if a_shoulder is not None and (a_shoulder is None or abs(a_shoulder - shoulder) > tolerance):
                #print(f"SHOULDER not within tolerance: current={a_shoulder}, target={shoulder}")
                time.sleep(0.1)
                continue

            if a_elbow is not None and (a_elbow is None or abs(a_elbow - elbow) > tolerance):
                #print(f"ELBOW not within tolerance: current={a_elbow}, target={elbow}")
                time.sleep(0.1)
                continue

            if a_tool is not None and (a_tool is None or abs(a_tool - tool) > tolerance):
                #print(f"TOOL not within tolerance: current={a_tool}, target={tool}")
                time.sleep(0.1)
                continue

            break

        #print(f"MoveAllJoints:   +-> reached target angles!")
        return True



    def _wait_for_reboot_finished(self, target_ip: str, timeout_seconds: int) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            response_time = ping(target_ip, unit='s', timeout=1)
            if response_time is not None and response_time is not False:
                return True
            else:
                time.sleep(1)
                
        return False