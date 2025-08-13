import cv2
import numpy as np
from ping3 import ping
import random as rng
import math


class OpenCV:
    def __init__(self, ip_address, timeout=3):
        self.ip_address = ip_address
        self.rtsp_url = f"rtsp://thingino:thingino@{self.ip_address}:554/ch0"
        self.timeout = timeout
        self.cap = None

        response_time = ping(ip_address, unit='s', timeout=1)
        if response_time is not None and response_time is not False:
            self.connected = True
            print(f"OpenCV initialized with IP: {self.ip_address}")
        else:
            self.connected = False
            print(f"OpenCV could not ping: {self.ip_address}")



    def _detectSpin(self, frame):

        # crop to interesting img only
        c_frame = frame[400:1000, 700:1400]
        #cv2.imshow('cropped', c_frame)

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
        #kernel = np.ones((3,3),np.uint8)
        #erode = cv2.erode(thresh, kernel, iterations = 1)
        #dilate = cv2.dilate(thresh, kernel, iterations = 1)
        #cv2.imshow('Erosion', cv2.erode(thresh, np.ones((3,3),np.uint8), iterations = 1))
        #cv2.imshow('Dilation', cv2.dilate(thresh, np.ones((3,3),np.uint8), iterations = 1))


        # detect edges with canny-algorithmn
        canny_output = cv2.Canny(thresh, 10, 100)
        
        # close open contours
        kernel = np.ones((3, 3), np.uint8)      # adjust size if needed
        closed = cv2.morphologyEx(canny_output, cv2.MORPH_CLOSE, kernel)

        # find contours
        closed_contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

        # ignore contours smaller than min_area
        min_area = 4000
        filtered_contours = [cnt for cnt in closed_contours if cv2.contourArea(cnt) > min_area]

        # make the hull of all contours
        all_points = np.vstack(filtered_contours)
        hull = cv2.convexHull(all_points)
        hull = hull.reshape(-1, 1, 2)      # ensure correct shape
        hull = hull.astype(np.int32)       # ensure correct type
        hull_contour = [hull]


        # draw the hull-courve
        #drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        #for i in range(len(hull_contour)):
        #    color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
        #    cv2.drawContours(drawing, hull_contour, i, color, 1, cv2.LINE_8, hierarchy, 0)
        #cv2.imshow('hull', drawing)
        
        # draw area-filtered contours
        #drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
        #for i in range(len(filtered_contours)):
        #    color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
        #    cv2.drawContours(drawing, filtered_contours, i, color, 1, cv2.LINE_8, hierarchy, 0)
        #cv2.imshow('contours', drawing)


        #clothespin_contour = None
        clothspin_contour_found = None
        clothespin_contours = hull_contour
        min_area = 25000
        max_area = 35000
        # 5. Konturen filtern (Beispiel: größte Kontur finden, die einer Wäscheklammer ähnelt)
        # Hier nehmen wir an, die Wäscheklammer ist das größte Objekt.
        # Sie müssen diesen Filter an Ihre spezifische Wäscheklammer und Umgebung anpassen.
        for contour in clothespin_contours:
            area = cv2.contourArea(contour)
            # Filtern nach Mindestgröße, um kleines Rauschen zu ignorieren
            if (area > min_area) and (area < max_area):
                # Optional: Überprüfen des Verhältnisses von Breite zu Höhe (Aspect Ratio)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                if 0.7 < aspect_ratio < 1.0:
                    clothspin_contour_found = contour
                    break


        if clothspin_contour_found is not None:
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
                return False
            
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.rtsp_url)

            if not self.cap.isOpened():
                print("Error: Cannot open RTSP stream")
                return False

            ret, frame = self.cap.read()
            if ret is None or frame is None:
                return False

        # detect object
        cropped_frame, rect, (cX, cY), angle = self._detectSpin(frame)

        # 7. Visualisierung
        box = cv2.boxPoints(rect)
        box = np.int_(box)
        cv2.drawContours(cropped_frame, [box], 0, (0, 255, 0), 2)
        cv2.circle(cropped_frame, (cX, cY), 7, (255, 0, 0), -1)
        cv2.putText(cropped_frame, f"center: ({cX}, {cY})", (cX + 10, cY + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(cropped_frame, f"angle: {angle:.2f} Grad", (cX + 10, cY + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        cv2.imshow('cropped', cropped_frame)



    def Close(self):
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()









if __name__ == "__main__":
    cam = OpenCV("192.168.1.122", 3)

    test_pic = cv2.imread('C:/workspace/SNsolutions/ClotheSpinAutomation/test_pic.png')

    cam.DetectClothespin(test_pic)
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cam.Close()
    exit()