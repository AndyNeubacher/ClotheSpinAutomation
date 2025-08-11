import keyboard
from RoboArm import RoArmM2S
from LightBurn import LightBurn
from ClotheSpin import ClotheSpin
from Tasmota import Tasmota
from time import sleep



if __name__ == "__main__":

    # Initialize devices

    air_assist = Tasmota("192.168.1.111", 3)
    air_assist.set_output(1, 'off')

    # Start LightBurn
    #laser = LightBurn("C:\\Program Files\\LightBurn\\LightBurn.exe", "localhost", 3)
    #if not laser.connected:
    #    print("Failed to connect to LightBurn. Exiting.")
    #    laser.Close()
    #    exit()

    #laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte")

    # Initialize RoArmM2S
    arm = RoArmM2S("192.168.1.121", 10)
    cspin = ClotheSpin(arm)
    if not cspin.connected:
        print("Failed to connect to RoArmM2S. Exiting.")
        exit()

    #cspin.CalibrateReferencePosition()
    #cspin._test_find_base_position()
    #arm.TeachMode()
    #exit()


    # Load LightBurn file
    #if not laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte"):
    #    print("Failed to load the LightBurn file. Exiting.")
    #    exit()


    # calibrate the zero-position robot-arm
    cspin.CalibrateReferencePosition()

    for i in range(0,51):
        if keyboard.is_pressed('esc'):
            print("ESC pressed, exiting loop.")
            break

        if cspin.Pick(i) == False:
            continue

        #cspin.MoveToBurnPosition()

        air_assist.set_output(1, 'on')
        #sleep(1)

        # 1st side burn
        #laser.Start()
        #if (laser.WaitForBurnFinished(300) == False):
        #    print("Burn failed or timed out.")
        #    break

        # 2nd side burn
        #cspin.FlipUpsideDown()
        #laser.Start()
        #if (laser.WaitForBurnFinished(300) == False):
        #    print("Burn failed or timed out.")
        #    break

        air_assist.set_output(1, 'off')

        cspin.MoveToFinishedPosition()


    # Cleanup
    air_assist.set_output(1, 'off')
    #laser.Close()