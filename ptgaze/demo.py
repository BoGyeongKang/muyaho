import time

import cv2
import logging
import numpy as np
import yacs.config

from ptgaze import (Face, GazeEstimationMethod, GazeEstimator, Visualizer)

MIN_PITCH = -8  # Down
MAX_PITCH = 5  # Up
MIN_YAW = -15
MAX_YAW = 15

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Demo:
    def __init__(self, config: yacs.config.CfgNode):
        self.config = config
        self.gaze_estimator = GazeEstimator(config)
        self.visualizer = Visualizer(self.gaze_estimator.camera)

        # Set Webcam
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.gaze_estimator.camera.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.gaze_estimator.camera.height)

        self.stop = False
        self.show_bbox = self.config.demo.show_bbox
        self.show_head_pose = self.config.demo.show_head_pose
        self.show_landmarks = self.config.demo.show_landmarks
        self.show_normalized_image = self.config.demo.show_normalized_image
        self.show_template_model = self.config.demo.show_template_model
        self.old_time = time.time()
        self.cheat = 0

    def process(self, frame):
        # Init cheat info
        self.cheat = 0

        # Detect face
        undistorted = cv2.undistort(frame, self.gaze_estimator.camera.camera_matrix, self.gaze_estimator.camera.dist_coefficients)
        self.visualizer.set_image(frame.copy())
        faces = self.gaze_estimator.detect_faces(undistorted)
        for face in faces:
            self.gaze_estimator.estimate_gaze(undistorted, face)
            self._calc_cheating(face)  # Calc cheat
        if not (len(faces) > 0):  # face not found
            self.cheat = 2

        cheat = self.cheat
        # img = self.visualizer.image

        return cheat

    # def run(self, client_socket) -> None:
    #     while True:
    #         ok, frame = self.cap.read()
    #         if not ok:
    #             break
    #         # Init cheat info
    #         self.cheat = 0
    #         # Detect face
    #         undistorted = cv2.undistort(frame, self.gaze_estimator.camera.camera_matrix, self.gaze_estimator.camera.dist_coefficients)
    #         self.visualizer.set_image(frame.copy())
    #         faces = self.gaze_estimator.detect_faces(undistorted)
    #         for face in faces:
    #             self.gaze_estimator.estimate_gaze(undistorted, face)
    #             self._calc_cheating(face)  # Calc cheat
    #         if not (len(faces) > 0):  # face not found
    #             self.cheat = 2
    #         # Send data to server
    #         self._send_data(client_socket)
    #     self.cap.release()

    def _calc_cheating(self, face: Face) -> None:
        if self.config.mode == GazeEstimationMethod.MPIIGaze.name:
            euler_angles = face.head_pose_rot.as_euler('XYZ', degrees=True)
            h_pitch, h_yaw, h_roll = face.change_coordinate_system(euler_angles)
            if not (MIN_PITCH <= h_pitch <= MAX_PITCH and MIN_YAW <= h_yaw <= MAX_YAW):
                self.cheat = 1

    def _send_data(self, client_socket):
        cheat = self.cheat
        img = self.visualizer.image

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, imgencode = cv2.imencode('.jpg', img, encode_param)

        data = np.array(imgencode)
        stringData = data.tobytes()

        message = '1'
        client_socket.send(message.encode())
        client_socket.send(str(cheat).ljust(16).encode())  # Send cheat info
        client_socket.send(str(len(stringData)).ljust(16).encode())  # Send image
        client_socket.send(stringData)
        data = client_socket.recv(1)
