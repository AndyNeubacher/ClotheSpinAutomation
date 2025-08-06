import time
from RoboArm import RoArmM2S
from RoboArm import Joint
import numpy as np

base_pos = [-177.0, -167.5, -160.5, -154.0, -147.0,
            -140.3, -135.3, -128.7, -121.0, -114.0, #10
            -106.5, -100.0,  -93.0,  -86.0,  -77.7,
             -70.6,  -63.5,  -56.4,  -49.3,  -42.2, #20
             -35.1,  -28.1,  -21.0,  -13.9,   -6.8,
               0.3,    7.4,   14.5,   21.6,   28.7, #30
              35.8,   42.9,   50.0,   57.1,   64.2,
              71.2,   78.3,   85.4,   92.5,   99.6, #40
             106.7,  113.8,  120.9,  128.0,  135.1,
             142.2,  149.3,  156.4,  163.5,  170.6, #50
             177.6,  184.7]



class ClotheSpin:
    """
    A Python class to control the Waveshare RoArm-M2-S robotic arm via Ethernet (HTTP).
    """

    def __init__(self, arm):
        self.RoboArm = arm
        self.connected = self.RoboArm.GetPosition() is not None
        self.last_angle_tool = None


    def IsConnected(self):
        return self.connected


    def OpenGripper(self, angle=20):
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.1)



    def CloseGripper(self, angle=5):
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.1)



    def MoveBaseToPosition(self, index):
        if self.RoboArm is None:
            return False

        print(f"ClothSpin: Moving base to position {index}...")
        self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos[index], speed=0.5, acc=10, tolerance=5, timeout=3)



    def MoveGripperToPosition(self, index):
        if self.RoboArm is None:
            return False

        print(f"ClothSpin: Moving gripper to position {index}...")
        return self.RoboArm.MoveAllJoints(base=base_pos[index], shoulder=30, elbow=140, tool=self.last_angle_tool, speed=0.5, tolerance=5, timeout=3)



    def Pick(self, index):
        if self.RoboArm is None:
            return False

        self.OpenGripper()

        self.MoveBaseToPosition(index)
        self.MoveGripperToPosition(index)

        self.CloseGripper()

