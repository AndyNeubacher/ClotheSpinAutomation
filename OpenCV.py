import cv2
import numpy as np
from ping3 import ping
import random as rng
import math
import time
import threading



class OpenCV:
    def __init__(self, ip_address, timeout=3):
        self.ip_address = ip_address
        self.rtsp_main_url = f"rtsp://thingino:thingino@{self.ip_address}:554/ch0"
        self.rtsp_sub_url = f"rtsp://thingino:thingino@{self.ip_address}/ch1"
        self.timeout = timeout
        self.cap = None

        response_time = ping(ip_address, unit='s', timeout=1)
        if response_time is not None and response_time is not False:
            self.connected = True
            print(f"OpenCV initialized with IP: {self.ip_address}")
        else:
            self.connected = False
            print(f"OpenCV could not ping: {self.ip_address}")


    def _crop_frame_per(self, frame, width_perc_start, width_perc_end, height_perc_start, height_perc_end):
        height, width, _ = frame.shape

        start_row = int(height * height_perc_start / 100)
        end_row = int(height * height_perc_end / 100)
        start_col = int(width * width_perc_start / 100)
        end_col = int(width * width_perc_end / 100)

        return frame[start_row:end_row, start_col:end_col]


    def _find_photobox(self, frame):
        return 35, 70, 40, 90

        height, width = frame.shape[:2]
        frame_area = height * width

        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.bilateralFilter(grey, 11, 21, 7)
        _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
        #cv2.imshow('thresh', thresh)

        canny_output = cv2.Canny(thresh, 10, 100)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        for i in range(len(filtered_contours)):
            color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
            cv2.drawContours(drawing, filtered_contours, i, color, 1, cv2.LINE_8, hierarchy, 0)
        cv2.imshow('contours', drawing)

        filtered_contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > frame_area*0.3) and (cv2.contourArea(cnt) < frame_area*0.8)]
        if len(filtered_contours) == 0:
            return None
        
        for contour in contours:
            # Calculate the area of the contour
            contour_area = cv2.contourArea(contour)

            # Calculate the area of the convex hull
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)

            # Avoid division by zero
            if hull_area > (frame_area * 0.4):
                solidity = float(contour_area) / hull_area
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.imshow('Found Black Box', frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()



    def _detectSpin(self, c_frame):
        # 1. Graustufenkonvertierung
        grey = cv2.cvtColor(c_frame, cv2.COLOR_BGR2GRAY)
        #cv2.imshow('grey', grey)
        
        # 2. Rauschunterdrückung (Gaußscher Weichzeichner)
        #blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        blurred = cv2.bilateralFilter(grey, 11, 21, 7)
        #cv2.imshow('blurred', blurred)

        # 3. Schwellenwertbildung (Otsu's Binarisierung ist oft gut)
        # Versuchen Sie, einen Schwellenwert zu finden, der die Wäscheklammer gut isoliert.
        _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_TRIANGLE)   #THRESH_TRIANGLE,THRESH_OTSU 
        #cv2.imshow('black-white', thresh)

        # Optional: Morphologische Operationen, um kleine Löcher zu schließen oder Objekte zu trennen
        kernel = np.ones((3,3),np.uint8)
        erode = cv2.erode(thresh, kernel, iterations = 1)
        #dilate = cv2.dilate(thresh, kernel, iterations = 1)
        #cv2.imshow('Erosion', cv2.erode(thresh, np.ones((3,3),np.uint8), iterations = 1))
        #cv2.imshow('Dilation', cv2.dilate(thresh, np.ones((3,3),np.uint8), iterations = 1))


        # detect edges with canny-algorithmn
        canny_output = cv2.Canny(thresh, 10, 100)
        
        # close open contours
        kernel = np.ones((3, 3), np.uint8)      # adjust size if needed
        closed = cv2.morphologyEx(canny_output, cv2.MORPH_CLOSE, kernel)
        #cv2.imshow('closed', closed)

        # find contours
        closed_contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

        # ignore contours smaller than min_area
        height, width = c_frame.shape[:2]
        frame_area = height * width
        min_area_per = frame_area * 0.02    # ignore shapes smaller than 2%
        max_area_per = frame_area * 0.30    # ignore shapes bigger than 30%
        filtered_contours = [cnt for cnt in closed_contours if (cv2.contourArea(cnt) > min_area_per) and (cv2.contourArea(cnt) < max_area_per)]
        if len(filtered_contours) == 0:
            return None

        # make the hull of all contours
        all_points = np.vstack(filtered_contours)
        hull_points = cv2.convexHull(all_points)
        hull_points = hull_points.reshape(-1, 1, 2)      # ensure correct shape
        hull_points = hull_points.astype(np.int32)       # ensure correct type
        hull_contours = [hull_points]


        # draw the hull-courve
        drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        for i in range(len(hull_contours)):
            color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
            cv2.drawContours(drawing, hull_contours, i, color, 1, cv2.LINE_8, hierarchy, 0)
        cv2.imshow('hull', drawing)
        
        # draw area-filtered contours
        #drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        #for i in range(len(filtered_contours)):
        #    color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
        #    cv2.drawContours(drawing, filtered_contours, i, color, 1, cv2.LINE_8, hierarchy, 0)
        #cv2.imshow('contours', drawing)


        #clothespin_contour = None
        clothspin_contour_found = None
        #min_area_per = 25000
        #max_area_per = 135000
        # 5. Konturen filtern (Beispiel: größte Kontur finden, die einer Wäscheklammer ähnelt)
        # Hier nehmen wir an, die Wäscheklammer ist das größte Objekt.
        # Sie müssen diesen Filter an Ihre spezifische Wäscheklammer und Umgebung anpassen.
        for contour in hull_contours:
            area = cv2.contourArea(contour)
            # Filtern nach Mindestgröße, um kleines Rauschen zu ignorieren
            if (area > min_area_per) and (area < max_area_per):
                # Optional: Überprüfen des Verhältnisses von Breite zu Höhe (Aspect Ratio)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                if 0.5 < aspect_ratio < 2:
                    clothspin_contour_found = contour
                    break

        if clothspin_contour_found is None:
            return None

        
        # 6. Berechnung von Mittelpunkt und Rotation
        # Mittelpunkt (Moment)
        M = cv2.moments(clothspin_contour_found)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0

        # Orientierung (Rotated Bounding Box)
        # Diese Box ist an die Kontur angepasst und gibt den Winkel.
        rect = cv2.minAreaRect(clothspin_contour_found)
        ((x, y), (width, height), angle) = rect

        # Anpassen des Winkels: minAreaRect gibt einen Winkel zwischen -90 und 0 Grad oder 0 und 90 Grad zurück,
        # abhängig von der Ausrichtung des Rechtecks. Möglicherweise müssen Sie ihn normalisieren.
        # Wenn die Breite größer als die Höhe ist, ist der Winkel der Winkel der Breite zur x-Achse.
        # Wenn die Höhe größer als die Breite ist, ist der Winkel 90 Grad plus der Winkel der Höhe zur x-Achse.
        if width < height:
            angle = angle + 90

        return c_frame, rect, (cX, cY) if clothspin_contour_found is not None else None, angle if clothspin_contour_found is not None else None



    def DetectClothespin(self, frame=None):
        # if no frame is provided, try to grab from the webcam
        if frame is None:
            if self.connected == False:
                return None
            
            if self.cap is None:
                # open the video-stream
                self.cap = cv2.VideoCapture(self.rtsp_main_url)

            if not self.cap.isOpened():
                print("Error: Cannot open RTSP stream")
                return None

            ret, frame = self.cap.read()
            if ret is None or frame is None:
                return None

            # close right after we got a valid frame
            self.cap.release()
            self.cap = None



        # crop to interesting region only
        res = self._find_photobox(frame)
        if res is not None:
            w_s, w_e, h_s, h_e = res
            cropped_frame = self._crop_frame_per(frame, w_s, w_e, h_s, h_e)#30, 70, 40, 90)

            # detect object
            res = self._detectSpin(cropped_frame)
            if res is not None:
                clip_frame, rect, (cX, cY), angle = res

                # 7. Visualisierung
                #box = cv2.boxPoints(rect)
                #box = np.int_(box)
                #cv2.drawContours(clip_frame, [box], 0, (0, 255, 0), 2)
                #cv2.circle(clip_frame, (cX, cY), 7, (255, 0, 0), -1)
                #cv2.putText(clip_frame, f"center: ({cX}, {cY})", (cX + 10, cY + 10),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                #cv2.putText(clip_frame, f"angle: {angle:.2f} Grad", (cX + 10, cY + 30),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                #cv2.imshow('cropped', clip_frame)       # show frame with bounding-box
                return res
            #else:
                #cv2.imshow('cropped', cropped_frame)    # show cropped frame without detection

        return None



    def Close(self):
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        self.cap = None







class LaserCam:
    def __init__(self, ip_address, timeout=3):
        self.running = False
        self.cam = OpenCV("192.168.1.122", 3)


    def Start(self):
        self.running = True
        while True:
            if self.cam.connected:
                self.cam.DetectClothespin()
                time.sleep(0.1)
                if self.running == False:
                    self.Close()


    def Close(self):
        self.running = False
        self.cam.Close()









if __name__ == "__main__":
    cam = OpenCV("192.168.1.122", 3)

    #test_pic = cv2.imread('C:/workspace/SNsolutions/ClotheSpinAutomation/test_pic.png')
    #cam.DetectClothespin(test_pic)

    while True:
        cam.DetectClothespin()
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cam.Close()
    exit()





    laser_cam = LaserCam("192.168.1.122", 3)
    cam_thread = threading.Thread(target=laser_cam.Start)
    cam_thread.start()


    #test_pic = cv2.imread('C:/workspace/SNsolutions/ClotheSpinAutomation/test_pic.png')
    #cam.DetectClothespin(test_pic)

    while True:
        #cam.DetectClothespin()
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    laser_cam.Close()
    cam_thread.join()
    