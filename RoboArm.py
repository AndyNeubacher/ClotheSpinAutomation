import requests
import json
import time
import sys
import threading
import msvcrt
import select

class RoArmM2S:
    """
    A Python class to control the Waveshare RoArm-M2-S robotic arm via Ethernet (HTTP).
    """

    def __init__(self, ip_address, timeout=10):
        """
        Initializes the RoArmM2S class.

        Args:
            ip_address (str): The IP address of the RoArm-M2-S.
                              If the WiFi is in AP mode, it's usually "192.168.4.1".
                              If in STA mode, check the OLED screen or your router.
            timeout (int): The timeout for HTTP requests in seconds.
        """
        self.ip_address = ip_address
        self.base_url = f"http://{self.ip_address}/cmd"
        self.timeout = timeout
        print(f"RoArm-M2-S initialized with IP: {self.ip_address}")


    def _send_command(self, command_data):
        """
        Sends a JSON command to the RoArm-M2-S via HTTP GET request.

        Args:
            command_data (dict): A dictionary representing the JSON command.

        Returns:
            dict or None: The JSON response from the robot, or None if an error occurred.
        """
        try:
            json_str = json.dumps(command_data)
            url = f"{self.base_url}?json={json_str}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()
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


    def get_status(self):
        """
        Gets the current status and joint angles of the robotic arm.

        Returns:
            dict or None: A dictionary containing feedback information, or None on failure.
                          Keys typically include 'base', 'shoulder', 'elbow', 'hand', etc.
        """
        command = {"T": 204}  # CMD_SERVO_RAD_FEEDBACK or similar (Waveshare doc has this)
        response = self._send_command(command)
        if response and response.get("status") == "ok":
            print(f"RoArm-M2-S Current Status: {response}")
            return response
        else:
            print("RoArm-M2-S: Failed to get status.")
            return None


    def _get_position(self):
        """
        Gets the current position of the robotic arm.

        Returns:
            dict or None: A dictionary containing the current XYZ position, or None on failure.
        """
        command = {"T": 205}
        response = self._send_command(command)




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

    def move_to_xyz(self, x=None, y=None, z=None, speed=500, mode=0):
        """
        Moves the end-effector to a specified 3D Cartesian coordinate using inverse kinematics.

        Args:
            x (float, optional): X coordinate in meters.
            y (float, optional): Y coordinate in meters.
            z (float, optional): Z coordinate in meters.
            speed (int, optional): Movement speed in steps/second (0 for max speed).
            mode (int, optional): 0 for linear movement, 1 for joint-space movement.
                                  (Check Waveshare doc for specific modes if any for this command)
        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        command = {"T": 103, "spd": speed, "mode": mode} # CMD_XYZT_GOAL_CTRL
        if x is not None:
            command["x"] = round(x, 4)
        if y is not None:
            command["y"] = round(y, 4)
        if z is not None:
            command["z"] = round(z, 4)

        response = self._send_command(command)
        return response is not None

    def set_gripper(self, angle, speed=500):
        """
        Controls the gripper/hand joint angle.

        Args:
            angle (float): Target angle for the gripper/hand in radians.
                           (clamp: 1.08 to 3.14, wrist: 1.08 to 5.20)
            speed (int, optional): Movement speed in steps/second (0 for max speed).
        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        # Note: The 'hand' parameter in move_to_joint_angles can also control the gripper.
        # This is a dedicated function for clarity.
        return self.move_to_joint_angles(hand=angle, speed=speed)


    def set_torque_lock(self, enable: bool):
        """
        Enables or disables the torque lock on the robotic arm.
        When torque lock is off, you can manually move the arm.

        Args:
            enable (bool): True to enable torque lock, False to disable.

        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        cmd_value = 1 if enable else 0
        command = {"T": 210, "cmd": cmd_value}
        response = self._send_command(command)
        return response is not None


    def set_led(self, enable: bool):
        """
        Turns the LED on or off.

        Args:
            enable (bool): True to turn LED on, False to turn LED off.

        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        led_value = 255 if enable else 0
        command = {"T": 114, "led": led_value}
        response = self._send_command(command)
        return response is not None

    def reset_to_initial_position(self):
        """
        Resets the robotic arm to its default initial position.

        Returns:
            bool: True if command sent successfully, False otherwise.
        """
        command = {"T": 100} # CMD_MOVE_INIT
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


    def teachMode(self):
        self.set_torque_lock(False)  # Disable torque lock to allow manual movement
        def _wait_for_exit():
            try:
                while True:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key in (b'\x1b', b'q', b'Q'):  # ESC or 'q'
                            print("RoArm-M2-S: Exiting teach mode.")
                            break
                    time.sleep(0.05)
                    print(self._get_position())

            except ImportError:
                print("RoArm-M2-S: Press ESC or 'q' to quit teach mode.")
                while True:
                    dr, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if dr:
                        ch = sys.stdin.read(1)
                        if ch in ('\x1b', 'q', 'Q'):
                            print("RoArm-M2-S: Exiting teach mode.")
                            break

        def teachMode(self):
            print("RoArm-M2-S: Teach mode started. Press ESC or 'q' to exit.")
            exit_event = threading.Event()
            t = threading.Thread(target=_wait_for_exit)
            t.start()
            t.join()

        self.set_torque_lock(True)