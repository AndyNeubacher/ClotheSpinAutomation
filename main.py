import keyboard
from RoboArm import RoArmM2S
from LightBurn import LightBurn
from ClotheSpin import ClotheSpin
from Tasmota import Tasmota




if __name__ == "__main__":

    # Initialize devices

    air_assist = Tasmota("192.168.1.141", 3)

    # Start LightBurn
    laser = LightBurn("C:\\Program Files\\LightBurn\\LightBurn.exe", "localhost", 3)
    if not laser.connected:
        print("Failed to connect to LightBurn. Exiting.")
        laser.Close()
        exit()

    laser.SelectAndLoadLightBurnFile("C:\\Users\\Administrator\\Google Drive\\Musi\\Laserprojekte")

    # Initialize RoArmM2S
    arm = RoArmM2S("192.168.1.140", 3)
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