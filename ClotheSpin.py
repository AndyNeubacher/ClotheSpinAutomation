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

#base_pos = [-179.0, -169.5, -162.5, -156.0, -149.0,
#-142.3, -137.3, -130.7, -123.0, -116.0,
#-108.5, -102.0,  -95.0,  -88.0,  -79.7,
# -72.6,  -65.5,  -58.4,  -51.3,  -44.2,
# -37.1,  -30.1,  -23.0,  -15.9,   -8.8,
#  -1.7,    5.4,   12.5,   19.6,   26.7,
#  33.8,   40.9,   48.0,   55.1,   62.2,
#  69.2,   76.3,   83.4,   90.5,   97.6,
# 104.7,  111.8,  118.9,  126.0,  133.1,
# 140.2,  147.3,  154.4,  161.5,  168.6,
# 175.6,  182.7]



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


    def OpenGripper(self, angle=15):
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)



    def CloseGripper(self, angle=1):
        print("ClothSpin: Opening gripper")
        self.last_angle_tool = 180 - angle
        self.RoboArm.SetGripper(self.last_angle_tool, speed=0.2)



    def MoveToPreparePosition(self, index):
        if self.RoboArm is None:
            return False

        print(f"ClothSpin: Moving base to position {index}...")
        #self.RoboArm.MoveSingleJoint(Joint.BASE.value, base_pos[index], speed=0.5, acc=10, tolerance=5, timeout=3)
        return self.RoboArm.MoveAllJoints(base=base_pos[index], shoulder=30, elbow=140, tool=self.last_angle_tool, speed=50, tolerance=5, timeout=5)



    def MoveGripperToClotheSpin(self, index):
        if self.RoboArm is None:
            return False

        print(f"ClothSpin: Moving gripper to position {index}...")
        return self.RoboArm.MoveAllJoints(base=base_pos[index], shoulder=41, elbow=132, tool=self.last_angle_tool, speed=30, tolerance=10, timeout=3)


    def MoveToBurnPosition(self):
        return self.RoboArm.MoveToXYZT(-40, -360, 0, self.last_angle_tool, 50, 10, 10)    


    def Pick(self, index):
        if self.RoboArm is None:
            return False

        # grab next item
        self.OpenGripper()
        self.MoveToPreparePosition(index)
        self.MoveGripperToClotheSpin(index)
        self.CloseGripper()

        # lift and drop
        self.RoboArm.MoveSingleJoint(Joint.SHOULDER.value, 25, speed=30, acc=10, tolerance=10, timeout=3)
        self.MoveToBurnPosition()
        self.OpenGripper()

