import os
import socket
import cv2
import datetime
import numpy as np
import threading
from _thread import *

video_path = 'C:/Users/Juhyun/Desktop/video/'

video_path = os.path.expanduser('~/Desktop/video/')
os.makedirs(video_path, exist_ok=True)

# 처음 시작할 때 DB에서 시험 아이디? 주소? 가져와서 exams 에 load
# candidates는 DB에서 load 할 때는 없다가 소켓 연결 들어오면 하나씩 추가하는 걸로
# supervisor에 socket도  연결 들어오면 추가
exams = [
    {'eid': '1', 'supervisor': ['uid0'], 'candidates': ['uid1', 'uid2', 'uid3'], 'start_time': '202105241330', 'end_time': '202105241500'},
    {'eid': '2', 'supervisor': ['uid4'], 'candidates': ['uid5', 'uid6', 'uid7'], 'start_time': '202105241400', 'end_time': '202105241600'},
    {'eid': '3', 'supervisor': ['uid8'], 'candidates': ['uid9', 'uid10', 'uid11'], 'start_time': '202105241400', 'end_time': '202105241600'}
]

port = 7777

lock = threading.Lock()


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def thread_webcam(client_socket, addr):
    port = 7777
    exam = None
    eid = None
    uid = None
    is_supervisor = False
    supervisor = None
    supervisor_socket = None

    print("CONNECTED BY : ", addr)

    # 응시자가 입력한 시험 주소 체크
    while True:
        exam_addr = client_socket.recv(1024).decode(encoding='ISO-8859-1')

        if any(exam['eid'] == exam_addr for exam in exams):

            eid = exam_addr
            exam = next(exam for exam in exams if exam['eid'] == exam_addr)
            supervisor = exam['supervisor']

            client_socket.send('1'.encode(encoding='ISO-8859-1'))

            uid = client_socket.recv(1024).decode(encoding='ISO-8859-1')

            if supervisor[0] == uid:
                is_supervisor = True
                supervisor.insert(1, client_socket)
                client_socket.send('1'.encode(encoding='ISO-8859-1'))

            else:
                tid = get_ident()  # 여러 명 접속 받을 때 비디오 파일 이름 겹치면 안되서 나중에 uid로 고치면 될 듯
                path = video_path + str(tid) + ".avi"
                fourcc = cv2.VideoWriter_fourcc(*'XVID')  # video codec
                out = cv2.VideoWriter(path, fourcc, 20.0, (640, 480))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

                exam['candidates'].insert(len(exam['candidates']), uid)
                client_socket.send('0'.encode(encoding='ISO-8859-1'))

            break

        # 응시자가 입력한 시험 주소가 exam_list 에 없는 경우
        else:
            client_socket.send('-1'.encode(encoding='ISO-8859-1'))
            continue

    while True:
        # supervisor[1] -> socket
        if is_supervisor == False and len(supervisor) != 1:
            client_socket.send('1'.encode(encoding='ISO-8859-1'))
            supervisor_socket = supervisor[1]
            break

    # 응시자로부터 웹 캠 영상 받고 감독관에게 전송
    while not is_supervisor:
        try:
            data = client_socket.recv(1).decode(encoding='ISO-8859-1')

            if not data:
                break

            length = client_socket.recv(16).decode(encoding='ISO-8859-1')
            stringData = recvall(client_socket, int(length))
            cheatData = client_socket.recv(16).decode(encoding='ISO-8859-1')  # Cheat info: 0 Normal 1 Cheat 2 NoFace

            client_socket.send('1'.encode(encoding='ISO-8859-1'))

            data = np.frombuffer(stringData, dtype='uint8')
            decimg = cv2.imdecode(data, 1)
            out.write(decimg)
            # cv2.imshow(str(tid), decimg)

            lock.acquire()
            supervisor_socket.send(uid.encode(encoding='ISO-8859-1'))
            supervisor_socket.send(str(len(stringData)).ljust(16).encode(encoding='ISO-8859-1'))
            supervisor_socket.send(stringData)
            supervisor_socket.send(cheatData.encode(encoding='ISO-8859-1'))  # Cheat info: 0 Normal 1 Cheat 2 NoFace
            supervisor_socket.recv(1).decode(encoding='ISO-8859-1')
            lock.release()

        except Exception as e:
            lock.release()
            supervisor.pop(1)
            break

    while is_supervisor:
        try:
            pass

        except Exception as e:
            supervisor.pop(1)
            break

    client_socket.close()
    print("DISCONNECT BY : ", addr)


def main():
    global port

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # SOCK.STREAM : TCP, SOCK.DGRAM : UDP
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', port))  # '' => INADDR_ANY

    print("WAITING FOR CLIENT...")

    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept()
        start_new_thread(thread_webcam, (client_socket, addr,))

    server_socket.close()


if __name__ == "__main__":
    main()
