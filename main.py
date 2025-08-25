import keyboard
from time import sleep
from RoboArm import RoArmM2S
from RoboArm import LogLevel
from LightBurn import LightBurn
from ClotheSpin import ClotheSpin
from Tasmota import Tasmota
from OpenCV import OpenCV
from Tools import Logging






if __name__ == "__main__":
    cam = air = laser = arm = cspin = log = None

    try:
        log = Logging(logfile_name='clothspin_log.txt')

        # Initialize devices
        cam = OpenCV("192.168.1.122", log, LogLevel.INFO, 3)
        if not cam.connected:
            raise Exception("Camera connection failed")

        # power-plug for air-compressor
        air = Tasmota("192.168.1.111", log, LogLevel.INFO, 1)
        air.SetOutput(1, 'off')

        # Start LightBurn
        laser = LightBurn("C:\\Program Files\\LightBurn\\LightBurn.exe", "localhost", log, LogLevel.INFO,  1)
        if not laser.connected:
            raise Exception("LightBurn connection failed")

        # Load LightBurn file
        #if not laser.SelectAndLoadLightBurnFile("C:\\Users\Administrator\\Google Drive\\Musi\\Laserprojekte\\RoArm", "Bierfluenza.lbrn2"):
        if not laser.SelectAndLoadLightBurnFile("C:\\Users\Administrator\\Google Drive\\Musi\\Laserprojekte\\RoArm"):
            raise Exception("Failed to load LightBurn file")

        # Initialize RoArmM2S
        arm = RoArmM2S("192.168.1.121", log, LogLevel.INFO, 5)
        cspin = ClotheSpin(arm, log, LogLevel.DEBUG)
        if not cspin.connected:
            raise Exception("ClotheSpin connection failed")

        # calibrate the zero-position robot-arm
        cspin.CalibrateReferencePosition()


        for i in range(0,51):
            if keyboard.is_pressed('esc'):
                raise Exception("Process interrupted by user")

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

            cspin.MoveToBurnPosition()
            air.SetOutput(1, 'on')

            # 1st side burn
            laser.Start()
            if (laser.WaitForBurnFinished(10, 300) == False):
                raise Exception("Burn failed or timed out")

            # 2nd side burn
            #cspin.FlipUpsideDown()
            #laser.Start()
            #if (laser.WaitForBurnFinished(300) == False):
            #    raise Exception("Burn failed or timed out")

            air.SetOutput(1, 'off')
            cspin.MoveToFinishedPosition()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Cleanup
        if air is not None: air.SetOutput(1, 'off')
        if cam is not None: cam.Close()
        if laser is not None: laser.Close()
        if log is not None: log.Close()