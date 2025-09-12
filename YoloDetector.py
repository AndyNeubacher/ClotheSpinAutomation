from datetime import datetime
from enum import Enum
import numpy as np
from ping3 import ping
from Tools import LogLevel
from Tools import Color
from Tools import Logging
#from ultralytics import YOLO
from roboflow import Roboflow
import supervision as sv
#from inference import get_model
import cv2


#pip install roboflow supervision
#pip install roboflow supervision opencv-python
#pip install inference supervision opencv-python ultralytics

# The model ID should be in the format "model_endpoint/version"
WORKSPACE_ID = "clothspindetector-n716n"
MODEL_ID = "clothspindetector-n716n/3"
#API_KEY = "hyav9bBDrlwRh16JGxo8"
API_KEY = "hyav9bBDrlwRh16JGxo8"

#https://universe.roboflow.com/foxdetector-xayxe/clothspindetector-n716n


class YoloDetector:
    def __init__(self, ip_address, logging=None, loglevel=LogLevel.NONE, timeout=3):
        self.ip_address = ip_address
        self.rtsp_main_url = f"rtsp://thingino:thingino@{self.ip_address}:554/ch0"
        self.rtsp_sub_url = f"rtsp://thingino:thingino@{self.ip_address}/ch1"
        self.timeout = timeout
        self.cap = None
        self.log = logging
        self.loglevel = loglevel

        response_time = ping(ip_address, unit='s', timeout=1)
        if response_time is not None and response_time is not False:
            self.connected = True
            self._log(f"OpenCV initialized with IP: {self.ip_address}", LogLevel.INFO)
        else:
            self.connected = False
            self._log(f"OpenCV could not ping: {self.ip_address}", LogLevel.ERROR)


    def _log(self, message, msg_level=None, color=None):
        if self.log is not None:
            self.log.PrintLog("OpenCV", message, msg_level, self.loglevel, Color.MAGENTA.value)


    def _find_photobox(self, frame):
        return 35, 70, 40, 90


    @Logging()
    def _crop_frame_per(self, frame, width_perc_start, width_perc_end, height_perc_start, height_perc_end):
        height, width, _ = frame.shape

        start_row = int(height * height_perc_start / 100)
        end_row = int(height * height_perc_end / 100)
        start_col = int(width * width_perc_start / 100)
        end_col = int(width * width_perc_end / 100)

        self._log(f"_crop_frame_per: width:{width} height:{height} start_row:{start_row} end_row:{end_row} start_col:{start_col} end_col:{end_col}", LogLevel.DEBUG)
        return frame[start_row:end_row, start_col:end_col]
    

    @Logging()
    def _detectSpin(self, c_frame):
        rf = Roboflow(api_key=API_KEY)
        project = rf.workspace().project(WORKSPACE_ID)
        model = project.version(3).model

        #print(model.predict(c_frame, confidence=40, overlap=30).json())

        result = model.predict(c_frame, confidence=40, overlap=30).json()
        if result is None or 'predictions' not in result or len(result['predictions']) == 0:
            self._log("No clothespin detected in cropped frame", LogLevel.INFO)
        
        if result.confidence > 0.7:
            self._log(f"clothespin detected with confidence of {result.confidence}", LogLevel.INFO)

        return None
        detections = sv.Detections.from_inference(result)
        bounding_box_annotator = sv.BoundingBoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        # Annotate the image
        annotated_image = bounding_box_annotator.annotate(
            scene=c_frame.copy(),
            detections=detections
        )
        annotated_image = label_annotator.annotate(
            scene=annotated_image,
            detections=detections
        )

        # 7. Display the annotated image
        cv2.imshow("Annotated Image", annotated_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        #detections = sv.Detections.from_ultralytics(result[0])
        #print(len(detections))

        # filter by class
        #detections = detections[detections.class_id == 0]
        #print(len(detections))
        return None



        model = get_model(model_id=MODEL_ID, api_key=API_KEY)
        results = model.infer(c_frame)[0]
        detections = sv.Detections.from_inference(results)

        bounding_box_annotator = sv.BoundingBoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        # Annotate the image
        annotated_image = bounding_box_annotator.annotate(
            scene=c_frame.copy(),
            detections=detections
        )
        annotated_image = label_annotator.annotate(
            scene=annotated_image,
            detections=detections
        )

        # 7. Display the annotated image
        cv2.imshow("Annotated Image", annotated_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        #self._log(f"Clothespin found at ({cX}, {cY}) with angle {angle:.2f} degrees", LogLevel.INFO)
        #return c_frame, rect, (cX, cY) if clothspin_contour_found is not None else None, angle if clothspin_contour_found is not None else None
        return None


    @Logging()
    def DetectClothespin(self, clip_idx=0, frame=None):
        # if no frame is provided, try to grab from the webcam
        if frame is None:
            if self.connected == False:
                return None
            
            if self.cap is None:
                # open the video-stream
                self._log(f"Opening RTSP stream: {self.rtsp_main_url}", LogLevel.INFO)
                self.cap = cv2.VideoCapture(self.rtsp_main_url)

            if not self.cap.isOpened():
                self._log("Error: Cannot open RTSP stream", LogLevel.ERROR)
                return None

            ret, frame = self.cap.read()
            if ret is None or frame is None:
                self._log("Error: Cannot read frame from RTSP stream", LogLevel.ERROR)
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
            dt_now = datetime.now()
            dt_now_str = dt_now.strftime("%Y-%m-%d_%H:%M:%S").replace(":", "-")

            res = self._detectSpin(cropped_frame)
            if res is not None:
                clip_frame, rect, (cX, cY), angle = res

                # 7. Visualisierung
                box = cv2.boxPoints(rect)
                box = np.int_(box)
                cv2.drawContours(clip_frame, [box], 0, (0, 255, 0), 2)
                cv2.circle(clip_frame, (cX, cY), 7, (255, 0, 0), -1)
                cv2.putText(clip_frame, f"center: ({cX}, {cY})", (cX + 10, cY + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(clip_frame, f"angle: {angle:.2f} Grad", (cX + 10, cY + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                #cv2.imshow('cropped', clip_frame)       # show frame with bounding-box
                if self.loglevel.value >= LogLevel.INFO.value:
                    cv2.imwrite(f'pic/found/{dt_now_str}_{clip_idx}.png', cropped_frame)
                return res
            else:
                self._log("No clothespin detected in cropped frame", LogLevel.ERROR)
                #cv2.imshow('cropped', cropped_frame)    # show cropped frame without detection
                if self.loglevel.value >= LogLevel.INFO.value:
                    cv2.imwrite(f'pic/not_found/{dt_now_str}_{clip_idx}.png', cropped_frame)

        return None
    






if __name__ == "__main__":
    log = Logging(logfile_name='opencv_log.txt')
    cam = YoloDetector("192.168.1.122", log, LogLevel.DEBUG, 3)

    test_pic = cv2.imread("C:\\tmp\\ClotheSpinAutomation\\pic\\not_found\\2025-09-06_12-03-09_2.png")
    cam._detectSpin(test_pic)

    while True:
        cam.DetectClothespin(test_pic)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cam.Close()
    exit()