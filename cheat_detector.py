import logging

import cv2

from ptgaze import Face, GazeEstimationMethod, GazeEstimator, get_default_config
from ptgaze.utils import update_default_config, update_config

MIN_PITCH = -8  # Down
MAX_PITCH = 5  # Up
MIN_YAW = -15
MAX_YAW = 15

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CheatDetector:
    def __init__(self, args):
        config = get_default_config()
        if args.config:
            config.merge_from_file(args.config)
            if (args.device or args.camera):
                raise RuntimeError('When using a config file, all the other commandline arguments are ignored.')
            if config.demo.image_path and config.demo.video_path:
                raise ValueError('Only one of config.demo.image_path or config.demo.video_path can be specified.')
        else:
            update_default_config(config, args)

        update_config(config)

        self.config = config
        self.gaze_estimator = GazeEstimator(config)

        self.cheat = 0

    def process(self, frame):
        # Init cheat info
        self.cheat = 0

        # Detect face
        undistorted = cv2.undistort(frame, self.gaze_estimator.camera.camera_matrix, self.gaze_estimator.camera.dist_coefficients)
        faces = self.gaze_estimator.detect_faces(undistorted)
        for face in faces:
            self.gaze_estimator.estimate_gaze(undistorted, face)
            self._calc_cheating(face)  # Calc cheat
        if not (len(faces) > 0):  # face not found
            self.cheat = 2

        cheat = self.cheat

        return cheat

    def _calc_cheating(self, face: Face) -> None:
        if self.config.mode == GazeEstimationMethod.MPIIGaze.name:
            euler_angles = face.head_pose_rot.as_euler('XYZ', degrees=True)
            h_pitch, h_yaw, h_roll = face.change_coordinate_system(euler_angles)
            if not (MIN_PITCH <= h_pitch <= MAX_PITCH and MIN_YAW <= h_yaw <= MAX_YAW):
                self.cheat = 1
