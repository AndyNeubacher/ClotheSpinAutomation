import time
import RoboArm
import numpy as np
from RoboArm import Joint
import msvcrt
import math

base_delta_pos = [   0.0,   6.8,  13.8,  20.9,  27.9,
                    None,  39.8,  46.9,  53.7,  60.9, #9
                    67.8,  74.8,  81.7,  88.8,  96.0,
                   103.1, 110.4, 117.4,  None, 129.3, #19
                   136.5, 143.5, 150.5, 158.0, 165.3,
                   172.4, 179.6, 186.8, 194.1, 201.4, #29
                   208.6,  None, 220.4, 227.5, 234.7,
                   241.6, 248.7, 255.9, 263.1, 270.1, #39 
                   277.4, 284.6, 291.7, 298.8,  None,
                   310.9, 318.0, 325.0, 331.7, 338.8, #49
                   346.0
]




class ClotheSpin:
    """
    A Python class to control the Waveshare RoArm-M2-S robotic arm via Ethernet (HTTP).
    """

    def __init__(self, arm):
        self.RoboArm = arm
        self.connected = self.RoboArm.GetPosition() is not None
        self.last_angle_tool = 180  # closed gripper
        self.cal_position = None
        self.cal_basepos_deg = None


    def _moveTo_PreparePosition(self, index):
        print(f"ClothSpin: Moving base to prepare-position {index}...")
        base_pos = self.cal_basepos_deg + base_delta_pos[index]
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 125, speed=50, acc=10, tolerance=2, timeout=2)
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 38, speed=50, acc=10, tolerance=2, timeout=2)
        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos, speed=50, acc=10, tolerance=0.2, timeout=2)
        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 0)


    def _moveTo_GripperToClotheSpin(self, index):
        print(f"ClothSpin: Moving gripper to position {index}...")
        base_pos = self.cal_basepos_deg + base_delta_pos[index]

        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 16)

        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos-0.5, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 132, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 42, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)

        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 0)


    def _test_find_base_position(self):
            pos = 26
            self.OpenGripper()
            self._moveTo_PreparePosition(pos)
            self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
            loop = True
            base_pos = 0
            while loop:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in (b'\x1b', b'q', b'Q'):  # ESC or 'q'
                        loop = False
                    if key in (b'+'):
                        if base_delta_pos[pos] is not None:
                            base_delta_pos[pos] += 0.1
                    if key in (b'-'):
                        if base_delta_pos[pos] is not None:
                            base_delta_pos[pos] -= 0.1
                    if key in (b' ') and base_delta_pos[pos] is not None:
                        if base_delta_pos[pos+1] == None:
                            self._moveTo_PreparePosition(pos+2)
                        else:
                            self._moveTo_PreparePosition(pos+1)
                        time.sleep(0.5)
            
                    # next/previous position
                    if key == b'\xe0':
                        key = msvcrt.getch()
                        if key == b'K' and pos > 0:
                            pos -= 1
                            if base_delta_pos[pos] is None:
                                pos -= 1    # skip None positions
                        elif key == b'M' and pos < len(base_delta_pos) - 1 :
                            pos += 1
                            if base_delta_pos[pos] is None:
                                pos += 1    # skip None positions

                if base_delta_pos[pos] is not None:
                    base_pos = self.cal_basepos_deg + base_delta_pos[pos]
                    self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 130, speed=50, acc=10, tolerance=0.5, timeout=1)
                    self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 39, speed=50, acc=10, tolerance=0.5, timeout=1)
                    self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos, speed=50, acc=10, tolerance=0.5, timeout=1)
                
                time.sleep(0.1)
                act_pos = self.RoboArm.GetAngle(Joint.BASE.value)
                print(f"ClothSpin: pos={pos}, array={base_delta_pos[pos]:.2f}, target={base_pos:.2f}, actual={act_pos:2f}")
                #print(self.RoboArm.GetPositionReadable())   


    def IsConnected(self):
        return self.connected


    def OpenGripper(self, angle=15):
        if self.RoboArm is None:
            return False
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)


    def CloseGripper(self, angle=1):
        if self.RoboArm is None:
            return False
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)


    def CalibrateReferencePosition(self):
        if self.RoboArm is None:
            return False
        # move to prepare position
        self.RoboArm.MoveToXYZT(x=-300, y=-40, z=-80, tool=90, speed=5, tolerance=10, timeout=5)
        self.RoboArm.SetDynamicForceAdaption(enable=True, base=100, shoulder=500, elbow=500, hand=500)
        # press gripper against the mechanical stop
        self.RoboArm.MoveSingleJointTorqueLimited(joint_id=Joint.BASE.value, angle=-180, speed=5, acc=5, max_torque=-50, timeout=1)
        time.sleep(0.5)
        # move arm to reference-end position
        self.RoboArm.MoveToXYZT(x=-320, y=-40, z=-120, tool=90, speed=10, tolerance=5, timeout=1)
        time.sleep(0.5)

        # disable force adaption, arm should settle down
        self.RoboArm.SetLed(True)
        self.RoboArm.SetTorqueLock(False)
        time.sleep(1)

        # now get calibration position
        self.cal_position = self.RoboArm.GetPosition()
        self.cal_basepos_deg = (self.cal_position['b'] * 180 / math.pi) 

        self.RoboArm.SetLed(False)
        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)
        self.RoboArm.SetTorqueLock(True)

        # now lift the arm to the prepare position
        print("ClothSpin: CALIBRATED-REFERENCE: " + self.RoboArm.GetPositionReadable())
        self.RoboArm.MoveAllJoints(base=self.cal_basepos_deg, shoulder=30, elbow=120, tool=90, speed=50, tolerance=5, timeout=1)
        self.OpenGripper()
        return self.cal_position


    def Pick(self, index):
        if self.RoboArm is None:
            return False
        if base_delta_pos[index] is None:
            print(f"ClothSpin: skip index {index}")
            return False

        # grab next item
        self._moveTo_PreparePosition(index)
        self.OpenGripper()
        self._moveTo_GripperToClotheSpin(index)
        self.CloseGripper()
        time.sleep(0.5)

        # now lift only in Z-axis with inverse kinematics
        pos = self.RoboArm.GetPosition()
        self.RoboArm.MoveToXYZT(pos['x'], pos['y'], pos['z'] + 50, self.last_angle_tool, speed=10, tolerance=5, timeout=1)


    def MoveToBurnPosition(self):
        if self.RoboArm is None:
            return False
        self.RoboArm.MoveToXYZT(-35, -360, 0, self.last_angle_tool, 50, 10, 10)
        self.OpenGripper()
        time.sleep(0.5)


    def MoveToFinishedPosition(self):
        self.MoveToBurnPosition()