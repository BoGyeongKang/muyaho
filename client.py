import sys

import socket
import threading

sys.path.insert(0, "./")
sys.path.insert(0, "../")

import argparse
import logging

from ptgaze.demo import Demo
from ptgaze import get_default_config
from ptgaze.utils import update_default_config, update_config

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help='Config file for YACS. When using a config file, all the other commandline arguments are ignored. See https://github.com/hysts/pytorch_mpiigaze_demo/configs/demo_mpiigaze.yaml')
    parser.add_argument('--mode', type=str, default='eye', choices=['eye', 'face'], help='With \'eye\', MPIIGaze model will be used. With \'face\', MPIIFaceGaze model will be used. (default: \'eye\')')
    parser.add_argument('--face-detector', type=str, default='face_alignment_sfd', choices=['dlib', 'face_alignment_dlib', 'face_alignment_sfd'], help='The method used to detect faces and find face landmarks (default: \'dlib\')')
    parser.add_argument('--device', type=str, choices=['cpu', 'cuda'], help='Device used for model inference.')
    parser.add_argument('--camera', type=str, help='Camera calibration file. See https://github.com/hysts/pytorch_mpiigaze_demo/ptgaze/data/calib/sample_params.yaml')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=7777)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger('ptgaze').setLevel(logging.DEBUG)

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
    logger.info(config)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((args.host, args.port))

    demo = Demo(config)
    webcam_thread = threading.Thread(target=demo.run, args=(client_socket,))
    webcam_thread.start()
    webcam_thread.join()
    client_socket.close()


if __name__ == '__main__':
    main()
