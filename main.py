import keyboard
from RoboArm import RoArmM2S
from LightBurn import LightBurn
from ClotheSpin import ClotheSpin
from Tasmota import Tasmota
from time import sleep
from OpenCV import OpenCV
import msvcrt
import threading




if __name__ == "__main__":

    # Initialize devices
    #cam = LaserCam("192.168.1.122", 3)
    #cam_thread = threading.Thread(target=cam.Start)
    #cam_thread.start()
    
    cam = OpenCV("192.168.1.122", 3)
    if not cam.connected:
        print("Failed to connect to WiFi camera. Exiting.")
        exit()

    # power-plug for air-compressor
    air_assist = Tasmota("192.168.1.111", 3)
    air_assist.set_output(1, 'off')

    # Start LightBurn
    #laser = LightBurn("C:\\Program Files\\LightBurn\\LightBurn.exe", "localhost", 3)
    #if not laser.connected:
    #    print("Failed to connect to LightBurn. Exiting.")
    #    laser.Close()
    #    exit()

    # Load LightBurn file
    #if not laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte"):
    #    print("Failed to load the LightBurn file. Exiting.")
    #    exit()


    # Initialize RoArmM2S
    arm = RoArmM2S("192.168.1.121", 10)
    cspin = ClotheSpin(arm)
    if not cspin.connected:
        print("Failed to connect to RoArmM2S. Exiting.")
        exit()

    # calibrate the zero-position robot-arm
    cspin.CalibrateReferencePosition()
    #cspin._test_find_base_position()
    #arm.TeachMode()
    #exit()

    for i in range(0,51):
        if keyboard.is_pressed('esc'):
            print("ESC pressed, exiting loop.")
            break

        if cspin.Pick(i) == False:
            continue

        cspin.MoveToOpticalInspection()

        # optical detection of the spin (max. 10 attempts)
        for i in range(5):
            frame = cam.DetectClothespin()
            if frame is not None:
                cspin.LedBlink(1, 0.5)
                break


        # lift out of the blackbox
        cspin.LiftFromOpticalInspection()

        # haven't found a clothespin -> move to waste-basket
        if frame is None:
            cspin.MoveToWastePosition()
            continue


        cspin.MoveToBurnPosition()  #570mm höhe

        air_assist.set_output(1, 'on')
        cspin.SetLed(True)
        sleep(1)
        cspin.SetLed(False)

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
    cam.Close()
    #laser.Close()