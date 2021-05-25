import socket
import cv2
import datetime
import numpy as np
import threading
from _thread import *

videoPath = 'C:/Users/owner/Desktop/video/'

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def thread_func(client_socket, addr):
    count = 0
    print("CONNECTED BY : ", addr)

    now = datetime.datetime.now()
    #tid = get_ident()   # thread id 이후에 서버에서 여러 명 접속 받을 때 비디오 파일 이름 겹치면 안되서 path를 thread id로 설정했었,,
    path = videoPath + now.strftime('%Y.%m.%d.%H.%M.%S') + ".avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')    # video codec
    out = cv2.VideoWriter(path, fourcc, 20.0, (640, 480))

    while True:
        try:
            data = client_socket.recv(1)
            if not data:
                print('DISCONNECTED BY ' + addr[0], ':', addr[1])
                break

            message = '1'
            cheat = recvall(client_socket, 16)
            print(int(cheat))
            length = recvall(client_socket, 16)
            stringData = recvall(client_socket, int(length))
            client_socket.send(message.encode())
            data = np.frombuffer(stringData, dtype='uint8')
            decimg = cv2.imdecode(data, 1)
            out.write(decimg)
            # # DEBUG
            if int(cheat) == 1:
                cv2.putText(decimg, 'CHEAT', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA)
            elif int(cheat) == 2:
                cv2.putText(decimg, 'No Face', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.imshow("Webcam", decimg)

            key = cv2.waitKey(1)
            if key == ord('q'):   # press q to exit
                print("DISCONNECT : ", addr)
                break

        except ConnectionResetError as e:
            print("DISCONNECT BY : ", addr)
            break

    client_socket.close()

port = 7777

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # SOCK.STREAM : TCP, SOCK.DGRAM : UDP
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', port))  # '' => INADDR_ANY


print("WAITING FOR CLIENT...")
server_socket.listen()
while True:
    client_socket, addr = server_socket.accept()
    start_new_thread(thread_func, (client_socket, addr,))


server_socket.close()