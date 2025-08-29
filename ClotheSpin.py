import time
import RoboArm
import numpy as np
from RoboArm import Joint
import msvcrt
import math
import Tools
from enum import Enum
from Tools import LogLevel
from Tools import Color
from Tools import Logging


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
                   346.0]

elbow_pos = [   136.0, 136.1, 136.2, 136.2, 136.3,
                136.4, 136.5, 136.6, 136.6, 136.7, #9
                136.8, 136.9, 137.0, 137.1, 137.2,
                137.3, 137.4, 137.4, 137.5, 137.6, #19
                137.7, 137.8, 137.9, 138.0, 138.0,
                138.0, 138.0, 137.9, 137.8, 137.7, #29
                137.6, 137.5, 137.4, 137.4, 137.3,
                137.2, 137.1, 137.0, 136.9, 136.8, #39
                136.7, 136.6, 136.6, 136.5, 136.4,
                136.3, 136.2, 136.2, 136.1, 136.0, #49
                136.0]

gripper_pick_offset = 0.2



class ClotheSpin:
    def __init__(self, arm=None, logging=None, loglevel=LogLevel.NONE):
        self.log = logging
        self.loglevel = loglevel
        self.RoboArm = arm
        self.last_angle_tool = 180  # closed gripper
        self.cal_position = None
        self.cal_basepos_deg = None
        self.connected = self.RoboArm.GetPosition() is not None
        self._log(f"ClothSpin bind to RoArm: {self.connected}", LogLevel.INFO)


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.Print("ClothSpin", message, msg_level, self.loglevel, Color.CYAN.value)


    @Logging()
    def _test_find_base_position(self):
            if self.RoboArm is None:
                return False

            self._log("ClothSpin: TEST-MODE: find base-position", LogLevel.INFO)
            pos = 26
            self.OpenGripper()
            self.MoveToPreparePosition(pos)
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
                            self.MoveToPreparePosition(pos+2)
                        else:
                            self.MoveToPreparePosition(pos+1)
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
                self._log(f"ClothSpin: pos={pos}, array={base_delta_pos[pos]:.2f}, target={base_pos:.2f}, actual={act_pos:2f}", LogLevel.INFO)


    def IsConnected(self):
        return self.connected


    @Logging()
    def OpenGripper(self, angle=15):
        if self.RoboArm is None:
            return False
        self._log("Opening gripper", LogLevel.INFO)
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)


    @Logging()
    def CloseGripper(self, angle=1):
        if self.RoboArm is None:
            return False
        self._log("Opening gripper", LogLevel.INFO)
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)


    @Logging()
    def SetLed(self, enable: bool):
        if self.RoboArm is None:
            return False
        self._log(f"Set LED: {'ON' if enable else 'OFF'}", LogLevel.INFO)
        self.RoboArm.SetLed(enable)


    @Logging()
    def LedBlink(self, cnt=1, interval=0.2):
        if self.RoboArm is None:
            return False
        self._log(f"LED blink {cnt} times with {interval}s interval", LogLevel.INFO)        
        for i in range(cnt):
            self.SetLed(True)
            time.sleep(interval)
            self.SetLed(False)
            time.sleep(interval)


    @Logging()
    def CalibrateReferencePosition(self):
        if self.RoboArm is None:
            return False

        self._log("ClothSpin: CALIBRATE-REFERENCE-POSITION", LogLevel.INFO)
        # move to prepare position
        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)
        self.RoboArm.MoveToXYZT(x=-50, y=-260, z=50, tool=127, speed=50, tolerance=50, timeout=3)
        #self.RoboArm.MoveToXYZT(x=-300, y=-40, z=-50, tool=127, speed=5, tolerance=2, timeout=3)
        self.RoboArm.MoveToXYZT(x=-260, y=-80, z=-50, tool=127, speed=5, tolerance=10, timeout=3)
        self.RoboArm.MoveToXYZT(x=-288, y=-43, z=-95, tool=127, speed=5, tolerance=5, timeout=3)

        self.RoboArm.SetDynamicForceAdaption(enable=True, base=300, shoulder=500, elbow=500, hand=500)
        # press gripper against the mechanical stop
        time.sleep(0.5)
        self.RoboArm.MoveSingleJointTorqueLimited(joint_id=Joint.BASE.value, angle=-180, speed=5, acc=5, max_torque=-50, timeout=1)
        time.sleep(1)
        # move arm to reference-end position
        self.RoboArm.MoveToXYZT(x=-320, y=-40, z=-120, tool=127, speed=10, tolerance=5, timeout=1.5)
        #time.sleep(0.5)

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
        self._log("CALIBRATED-REFERENCE: " + self.RoboArm.GetPositionReadable(), LogLevel.INFO)
        self.RoboArm.MoveAllJoints(base=self.cal_basepos_deg, shoulder=30, elbow=120, tool=127, speed=50, tolerance=5, timeout=1)
        self.OpenGripper()
        return self.cal_position


    @Logging()
    def Pick(self, index):
        if self.RoboArm is None:
            return False
        
        self._log(f"Pick index {index}", LogLevel.INFO)
        if base_delta_pos[index] is None:
            self._log(f"skipped index {index}", LogLevel.INFO)
            return False

        # grab next item
        self.MoveToPreparePosition(index)
        self.OpenGripper()
        self.MoveToGripperToClotheSpin(index)

        self.RoboArm.SetDynamicForceAdaption(enable=True, base=10, shoulder=10, elbow=10, hand=500)
        self.CloseGripper()
        time.sleep(0.5)

        # now lift only in Z-axis with inverse kinematics
        pos = self.RoboArm.GetPosition()

        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)
        self.RoboArm.MoveToXYZT(pos['x'], pos['y'], pos['z'] + 20, self.last_angle_tool, speed=5, tolerance=5, timeout=2)
        self.RoboArm.MoveToXYZT(pos['x'], pos['y'], pos['z'] + 50, self.last_angle_tool, speed=30, tolerance=5, timeout=1)
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 155, speed=50, acc=10, tolerance=5, timeout=1)


    @Logging()
    def MoveToPreparePosition(self, index):
        if self.RoboArm is None:
            return False
        
        self._log(f"Moving base to prepare-position {index}", LogLevel.INFO)
        base_pos_offset = self.cal_basepos_deg + base_delta_pos[index] + gripper_pick_offset
        self.RoboArm.MoveAllJoints(base=base_pos_offset, shoulder=35, elbow=125, tool=self.last_angle_tool, speed=50, tolerance=2, timeout=3)
        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos_offset, speed=50, acc=10, tolerance=0.2, timeout=2)


    @Logging()
    def MoveToGripperToClotheSpin(self, index):
        if self.RoboArm is None:
            return False
        
        self._log(f"Moving gripper to position {index}", LogLevel.INFO)
        base_pos = self.cal_basepos_deg + base_delta_pos[index] 

        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 16)

        # move base+elbow over clothe-spin (base with offset)
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos+gripper_pick_offset, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)

        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, elbow_pos[index], speed=20, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)

        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=5, elbow=100, hand=500)

        # lower shoulder with very less force
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 42, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)

        # now center base to correct position (without offset ... 0.2 -> just a little bit more to the other side!)
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos-0.5, speed=50, acc=10, tolerance=0.2, timeout=2)
        time.sleep(0.5)

        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 137, speed=50, acc=10, tolerance=1, timeout=1)
        time.sleep(0.5)

        self.RoboArm.SetTorqueLock(False)
        time.sleep(1)

        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 0)
        self.RoboArm.SetTorqueLock(True)



    @Logging()
    def MoveToOpticalInspection(self):
        if self.RoboArm is None:
            return False

        self._log("Move to optical inspection position", LogLevel.INFO)

        self.RoboArm.MoveToXYZT(125, -120, -75, self.last_angle_tool, 50, 20, 5)
        #self.RoboArm.MoveSingleJoint(Joint.BASE.value, -50, speed=50, acc=10, tolerance=5, timeout=3)
        self.RoboArm.MoveToXYZT(210, -195, 50, self.last_angle_tool, 50, 20, 5)
        time.sleep(0.5)
        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 16)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 16)
        #self.RoboArm.MoveToXYZT(250, -238, -100, self.last_angle_tool, 1, 20, 5)
        self.RoboArm.MoveToXYZT(230, -235, -95, self.last_angle_tool, 1, 20, 5)
        #time.sleep(0.5)
        #self.OpenGripper()
        #time.sleep(0.5)
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 106, speed=10, acc=10, tolerance=1, timeout=2)
        self.RoboArm.SetTorqueLock(False)



    @Logging()
    def MoveToBurnPosition(self):
        if self.RoboArm is None:
            return False
        
        self._log("Move to burn position", LogLevel.INFO)

        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 0)

        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)

        self.RoboArm.MoveSingleJoint(Joint.BASE.value, -42, speed=50, acc=10, tolerance=1, timeout=3) #42.5
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 150, speed=50, acc=10, tolerance=5, timeout=3)
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, -45, speed=50, acc=10, tolerance=1, timeout=3)
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 43, speed=50, acc=10, tolerance=1, timeout=5)   #44
        time.sleep(0.5)



    @Logging()
    def MoveToFinishedPosition(self):
        if self.RoboArm is None:
            return False
        
        self._log("Move to finished position", LogLevel.INFO)
        self.RoboArm.MoveSingleJoint(Joint.ELBOW.value, 150, speed=50, acc=10, tolerance=5, timeout=3)
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 0, speed=50, acc=10, tolerance=5, timeout=3)
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, -85, speed=50, acc=10, tolerance=5, timeout=3)
        self.RoboArm.MoveToXYZT(-35, -360, 0, self.last_angle_tool, 50, 10, 10)
        self.OpenGripper()
        time.sleep(0.5)



    @Logging()
    def MoveToWastePosition(self):
        if self.RoboArm is None:
            return False

        self._log("Move to waste position", LogLevel.INFO)
        self.MoveSingleJoint(Joint.SHOULDER.value, angle=10, speed=20, acc=5, tolerance=10, timeout=2)
        self.MoveSingleJoint(Joint.ELBOW.value, angle=150, speed=20, acc=5, tolerance=10, timeout=2)

        pos = self.RoboArm.GetPosition()
        self.RoboArm.MoveToXYZT(pos['x'], pos['y'], 50, self.last_angle_tool, speed=0.1, tolerance=50, timeout=3)
        self.RoboArm.MoveToXYZT(-260, -250, 50, self.last_angle_tool, 50, 50, 3)
        self.OpenGripper()
        time.sleep(0.5)


    @Logging()
    def LiftFromOpticalInspection(self):
        if self.RoboArm is None:
            return False

        self._log("Lift from optical inspection", LogLevel.INFO)
        self.RoboArm.SetJointPID(Joint.BASE.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.ELBOW.value, 16, 0)
        self.RoboArm.SetJointPID(Joint.SHOULDER.value, 16, 0)
        self.RoboArm.SetTorqueLock(True)
        self.CloseGripper()
        pos = self.RoboArm.GetPosition()
        self.RoboArm.SetDynamicForceAdaption(enable=True, base=500, shoulder=500, elbow=500, hand=500)
        self.RoboArm.MoveToXYZT(pos['x'], pos['y'], 100, self.last_angle_tool, speed=10, tolerance=20, timeout=3)