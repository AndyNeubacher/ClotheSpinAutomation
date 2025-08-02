import keyboard
from RoboArm import RoArmM2S
from LightBurn import LightBurn
from ClotheSpin import ClotheSpin
from Tasmota import Tasmota
from time import sleep



if __name__ == "__main__":

    # Initialize devices

    #air_assist = Tasmota("192.168.1.141", 3)

    # Start LightBurn
    #laser = LightBurn("C:\\Program Files\\LightBurn\\LightBurn.exe", "localhost", 3)
    #if not laser.connected:
    #    print("Failed to connect to LightBurn. Exiting.")
    #    laser.Close()
    #    exit()

    #laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte")

    # Initialize RoArmM2S
    arm = RoArmM2S("192.168.1.173", 10)
    arm.InitPosition()

    #arm.SetJointPID(1, 10, 0)  # Set PID for elbow joint
    #arm.SetJointPID(2, 10, 0)  # Set PID for elbow joint
    #arm.SetJointPID(3, 10, 0)  # Set PID for elbow joint
    #arm.SetJointPID(4, 10, 0)  # Set PID for elbow joint
    #arm.SetDynamicForceAdaption(True, 1000, 1000, 1000, 1000)  # Enable dynamic adaption force

    #arm.SetGripper(10)
    #sleep(2)
    #arm.TeachMode()
    pos = arm.GetPositionReadable()
    print(f"Current position: {pos}")
    #exit()

    for _ in range(10):
        arm.MoveToXYZ(285, 218, -110, 20, 1000)
        sleep(1)
        arm.SetGripper(5)
        sleep(1)

        arm.MoveToXYZ(230, 250, -50, 5, 1000)
        sleep(1)

        arm.MoveToXYZ(190, 300, -110, 5, 1000)
        sleep(1)
        arm.SetGripper(20)
        sleep(1)

        arm.MoveToXYZ(230, 250, -50, 20, 1000)
        sleep(1)

    exit()



    cspin = ClotheSpin(arm)
    if not cspin.connected:
        print("Failed to connect to RoArmM2S. Exiting.")
        exit()




    # Load LightBurn file
    if not laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte"):
        print("Failed to load the LightBurn file. Exiting.")
        exit()


    # load file to lightburn and init robot-arm
    cspin.InitPosition()


    for _ in range(50):
        if keyboard.is_pressed('esc'):
            print("ESC pressed, exiting loop.")
            break

        cspin.PickNew()

        air_assist.set_output(1, 'on')

        # 1st side burn
        laser.Start()
        if (laser.WaitForBurnFinished(300) == False):
            print("Burn failed or timed out.")
            break

        # 2nd side burn
        cspin.FlipUpsideDown()
        laser.Start()
        if (laser.WaitForBurnFinished(300) == False):
            print("Burn failed or timed out.")
            break

        air_assist.set_output(1, 'off')

        cspin.MoveToFinishedPosition()


    # Cleanup
    air_assist.set_output(1, 'off')
    laser.Close()