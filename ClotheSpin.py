import time


class ClotheSpin:
    """
    A Python class to control the Waveshare RoArm-M2-S robotic arm via Ethernet (HTTP).
    """

    def __init__(self, arm):
        self.RoboArm = arm
        self.connected = self.InitPosition()


    def IsConnected(self):
        return self.connected


    def InitPosition(self):
        if self.RoboArm is None:
            return False

        print("ClothSpin: Attempting to connect and get status...")
        status = self.RoboArm.get_status()
        if status:
            print("ClothSpin: Successfully connected and received status.")
        else:
            print("ClothSpin: Failed to connect or get status. Exiting example.")
            return False

        time.sleep(1) # Give it a moment

        print("ClothSpin: Resetting arm to initial position...")
        if self.RoboArm.reset_to_initial_position():
            print("ClothSpin: Arm reset command sent.")
        else:
            print("ClothSpin: Failed to send reset command.")
            return False
        
        time.sleep(3) # Wait for movement to complete
        return True


    def PickNew(self):
        if self.RoboArm is None:
            return False

        print("ClothSpin: Opening gripper...")
        self.RoboArm.set_gripper(angle=45, speed=300) # Larger angle for clamp means more open
        time.sleep(2)

        print("ClothSpin: Moving arm to a new joint configuration...")
        if self.RoboArm.move_to_xyz(x=0.2, y=0.05, z=0.1, speed=600):
            print("ClothSpin: Joint movement command sent.")
        else:
            print("ClothSpin: Failed to send joint movement command.")
        time.sleep(3)

        print("ClothSpin: Close gripper...")
        self.RoboArm.set_gripper(angle=10, speed=300)
        time.sleep(2)
        return True


    def MoveToBurnPosition(self):
        if self.RoboArm is None:
            return False

        print("ClothSpin: Moving arm to work position...")
        # Example work position angles
        if self.RoboArm.move_to_xyz(x=0.2, y=0.05, z=0.1, speed=600):
            print("ClothSpin: Work position command sent.")
        else:
            print("ClothSpin: Failed to send work position command.")
        time.sleep(3)
        return True


    def FlipUpsideDown(self):
        if self.RoboArm is None:
            return False

        print("ClothSpin: Flipping arm upside down...")
        # Example flip position angles
        if self.RoboArm.move_to_xyz(x=0.2, y=0.05, z=0.1, speed=600):
            print("ClothSpin: Flip command sent.")
        else:
            print("ClothSpin: Failed to send flip command.")
        time.sleep(3)
        return True


    def MoveToFinishedPosition(self):
        if self.RoboArm is None:
            return False

        print("ClothSpin: Moving arm to finished position...")
        # Example finished position angles
        if self.RoboArm.move_to_xyz(x=0.2, y=0.05, z=0.1, speed=600):
            print("ClothSpin: Finished position command sent.")
        else:
            print("ClothSpin: Failed to send finished position command.")
        time.sleep(3)

        self.RoboArm.set_gripper(angle=45, speed=300)  # Open gripper to release the clothespin
        time.sleep(2)

        return True