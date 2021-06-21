import argparse
import sys, sqlite3
import socket
import threading
import cv2
import numpy as np
import re
from datetime import datetime
import time

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QDialog, QMessageBox, QBoxLayout, QListWidgetItem, QListWidget, QInputDialog
from PyQt5 import uic

from cheat_detector import CheatDetector


first_ui = uic.loadUiType("first.ui")[0]
createExam_ui = uic.loadUiType("createExam.ui")[0]
prepareExam_ui = uic.loadUiType("prepareexam2.ui")[0]
takeExam_ui = uic.loadUiType("takeexam2.ui")[0]

uid = None


# 로그인창
class Login(QWidget, first_ui):
    def __init__(self):
        super(Login, self).__init__()
        self.signUppage = None
        self.myStartpage = None
        self.initUI()

    def initUI(self):
        self.setupUi(self)
        self.btn_signup.clicked.connect(self.create_signUp)
        self.btn_login.clicked.connect(self.create_start)

    def create_signUp(self):
        if self.signUppage is None:
            self.signUppage = SignUp(self)

        self.signUppage.show()

    def create_start(self):

        ###########################
        uid = self.idEdit.text()
        pw = self.pwEdit.text()
        queue = []
        str = 'login@' + uid + '@' + pw

        thread_socket_login = thread_socket_GUI(self, server_socket, str, queue)
        thread_socket_login.start()
        time.sleep(0.5)

        result = queue.pop()

        if result == '1':
            print("로그인성공")
            w_login.hide()
            if self.myStartpage is None:
                self.myStartpage = myStart(self)
            self.myStartpage.show()
        else:
            QMessageBox.about(self, "로그인실패", "아이디와 비밀번호가 일치하지 않습니다")
        ###########################


# 회원가입창
class SignUp(QDialog):
    def __init__(self, *args, **kwargs):
        super(SignUp, self).__init__(*args, **kwargs)
        self.sqlConnect()
        self.initUI()

    def sqlConnect(self):
        try:
            self.conn = sqlite3.connect("test1.db")
        except:
            print("DB연동에 문제가 생겼습니다ㅠㅠ")
            exit(1)

    def initUI(self):
        btn_signup = QPushButton('회원가입하기', self)
        btn_signup.resize(btn_signup.sizeHint())
        btn_signup.move(20, 30)
        btn_signup.clicked.connect(self.signUp)

        id = QLabel('id')
        pw = QLabel('password')
        phonenum = QLabel('phone number')

        self.edit_id = QLineEdit(self)
        self.edit_pw = QLineEdit(self)
        self.edit_phonenum = QLineEdit(self)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(id, 1, 0)
        grid.addWidget(self.edit_id, 1, 1)
        grid.addWidget(pw, 2, 0)
        grid.addWidget(self.edit_pw, 2, 1)
        grid.addWidget(phonenum, 3, 0)
        grid.addWidget(self.edit_phonenum, 3, 1)

        self.setLayout(grid)

        self.setGeometry(300, 300, 400, 500)
        self.setWindowTitle('회원가입하기')
        self.show()

    def signUp(self):

        ###########################
        uid = self.edit_id.text()
        pw = self.edit_pw.text()
        phoneNum = self.edit_phonenum.text()
        str = 'signUp@' + uid + '@' + pw + '@' + phoneNum + '@'

        thread_socket_signUp = thread_socket_GUI(self, server_socket, str, None)
        thread_socket_signUp.start()
        time.sleep(0.3)

        self.hide()
        ###########################

    def closeEvent(self, QCloseEvent):
        print("프로그램 close!")
        self.conn.close()


# 로그인 성공시 메인창
class myStart(QDialog):
    def __init__(self, *args, **kwargs):
        super(myStart, self).__init__(*args, **kwargs)
        self.createExampage = None
        self.enterExampage = None
        # self.sqlConnect()
        self.initUI()

    def initUI(self):
        btn_prepare = QPushButton('시험출제하기', self)
        btn_prepare.resize(btn_prepare.sizeHint())
        btn_prepare.move(20, 30)
        btn_prepare.clicked.connect(self.createExam)

        btn_enter = QPushButton('시험응시하기', self)
        btn_enter.resize(btn_enter.sizeHint())
        btn_enter.move(20, 60)
        btn_enter.clicked.connect(self.enterExam)

        self.setGeometry(300, 300, 400, 500)
        self.setWindowTitle('부정행위 방지 시험 프로그램')
        self.show()

    def set_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', type=str, help='Config file for YACS. When using a config file, all the other commandline arguments are ignored. See https://github.com/hysts/pytorch_mpiigaze_demo/configs/demo_mpiigaze.yaml')
        parser.add_argument('--mode', type=str, default='eye', choices=['eye', 'face'], help='With \'eye\', MPIIGaze model will be used. With \'face\', MPIIFaceGaze model will be used. (default: \'eye\')')
        parser.add_argument('--face-detector', type=str, default='face_alignment_sfd', choices=['dlib', 'face_alignment_dlib', 'face_alignment_sfd'], help='The method used to detect faces and find face landmarks (default: \'dlib\')')
        parser.add_argument('--device', type=str, choices=['cpu', 'cuda'], help='Device used for model inference.')
        parser.add_argument('--camera', type=str, help='Camera calibration file. See https://github.com/hysts/pytorch_mpiigaze_demo/ptgaze/data/calib/sample_params.yaml')
        parser.add_argument('--host', type=str, default='127.0.0.1')
        parser.add_argument('--port', type=int, default=7777)
        args = parser.parse_args()

        return args

    def createExam(self):
        print("시험출제")
        if self.createExampage is None:
            self.createExampage = createExam(self)
        self.createExampage.show()

    def enterExam(self):
        print("시험응시")
        global eid

        text, ok = QInputDialog.getInt(self, "시험코드", "시험코드를 입력하세요.")
        queue = []
        string = 'enterExam@' + str(text)

        thread_socket_enter = thread_socket_GUI(self, server_socket, string, queue)
        thread_socket_enter.start()
        time.sleep(0.5)

        result = queue.pop()

        # 1이면 감독관, 0이면 응시자, -1이면 시험코드 잘못됨
        if result == '1':
            receive_webcam_thread = threading.Thread(target=thread_receive_webcam, args=(server_socket,))
            receive_webcam_thread.start()
            receive_webcam_thread.join()

        elif result == '0':
            args = self.set_args()
            send_webcam_thread = threading.Thread(target=thread_send_webcam, args=(server_socket, args))
            send_webcam_thread.start()
            self.enterExampage = takeExam(self)
            self.enterExampage.show()
            send_webcam_thread.join()

        else:
            pass

        if ok:
            eid = str(text)
        if self.enterExampage is None:
            self.enterExampage = takeExam(self)
        self.enterExampage.show()

    def closeEvent(self, QCloseEvent):
        print("프로그램 close!")
        self.conn.close()


# 시험생성_eid생성
class createExam(QDialog, createExam_ui):
    def __init__(self, *args, **kwargs):
        super(createExam, self).__init__(*args, **kwargs)
        self.prepareExampage = None
        self.sqlConnect()
        self.initUI()

    def sqlConnect(self):
        try:
            self.conn = sqlite3.connect("test1.db")
        except:
            print("DB연동에 문제가 생겼습니다ㅠㅠ")
            exit(1)

    def initUI(self):
        self.setupUi(self)
        self.btn_create.clicked.connect(self.createEid)

    def createEid(self):
        global eid
        print("eid생성 성공")
        self.cur = self.conn.cursor()
        # sql = "insert into Exam(eid,startdate,enddate,starttime,endtime,uid) values (?,?,?,?,?,?)"
        a = self.startTime.date().toString("yyyyMMdd")
        b = self.endTime.date().toString("yyyyMMdd")
        c = self.startTime.time().toString("HHmmss")
        d = self.endTime.time().toString("HHmmss")
        eid = self.eid_Edit.text()
        # self.cur.execute(sql, (eid, a, b, c, d, "uid"))

        string = 'createExam@' + str(eid) + '@' + a + '@' + c + '@' + b + '@' + d
        print(string)
        thread_socket_createExam = thread_socket_GUI(self, server_socket, string, None)
        thread_socket_createExam.start()

        time.sleep(0.3)

        # 과목테이블 생성
        # self.cur.execute('create table ' + eid + '(problemNum text, question text,answer text)')
        # self.conn.commit()

        self.hide()
        if self.prepareExampage is None:
            self.prepareExampage = prepareExam(self)
        self.prepareExampage.show()

    def closeEvent(self, QCloseEvent):
        print("프로그램 close!")
        self.conn.close()


# 시험문제출제
class prepareExam(QDialog, prepareExam_ui):
    def __init__(self, *args, **kwargs):
        super(prepareExam, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        global problemNum
        problemNum = 1

        self.setupUi(self)

        self.next_btn.clicked.connect(self.next)
        self.done_btn.clicked.connect(self.done)

    def next(self):
        print("다음문제")
        global problemNum

        self.conn = sqlite3.connect("test1.db")
        self.cur = self.conn.cursor()
        sql = "insert into " + eid + "(problemNum,question,answer) values (?,?,?)"
        question = self.question_Edit.text()
        answer = self.answer_Edit.text()
        # self.cur.execute(sql, (problemNum, question, answer))
        # self.conn.commit()

        string = 'newProblem@' + str(problemNum) + '@' + question + '@' + answer

        thread_socket_problem = thread_socket_GUI(self, server_socket, string, None)
        thread_socket_problem.start()
        time.sleep(0.3)

        item = QListWidgetItem(self.listWidget)
        custom_widget = Item()
        item.setSizeHint(custom_widget.sizeHint())
        self.listWidget.setItemWidget(item, custom_widget)
        self.listWidget.addItem(item)

        problemNum = problemNum + 1
        self.question_Edit.clear()
        self.answer_Edit.clear()

    def done(self):
        print("시험출제완료")

        thread_socket_complete = thread_socket_GUI(self, server_socket, 'complete@', None)
        thread_socket_complete.start()
        time.sleep(0.3)

        self.hide()

    def closeEvent(self, QCloseEvent):
        print("프로그램 close!")
        self.conn.close()


class Item(QWidget):
    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        layout = QBoxLayout(QBoxLayout.TopToBottom)
        pbtext = "Q." + str(problemNum)
        self.pb = QPushButton(pbtext)
        layout.addWidget(self.pb)
        layout.setSizeConstraint(QBoxLayout.SetFixedSize)
        self.setLayout(layout)
        self.pb.clicked.connect(self.changePos)

    def changePos(self):
        global nowpos
        nowpos = int(self.pb.text().replace("Q.", "")) - 1
        global questionBrowser
        global result
        questionBrowser.setText(result[nowpos][1])


# 시험응시창
class takeExam(QDialog, takeExam_ui):
    def __init__(self, *args, **kwargs):
        # self.sqlConnect()
        super(takeExam, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        global problemNum
        problemNum = 1

        # print(eid)
        self.setupUi(self)

        try:
            self.conn = sqlite3.connect('test1.db')
        except:
            print("DB연동에 문제가 생겼습니다ㅠㅠ")
            exit(1)
        print("DB연동성공!")
        self.cur = self.conn.cursor()
        sql = "SELECT * FROM " + eid
        self.cur.execute(sql)
        global result
        self.result = self.cur.fetchall()
        result = self.result

        for i in range(1, len(self.result) + 1):
            item = QListWidgetItem(self.listWidget)
            custom_widget = Item()
            item.setSizeHint(custom_widget.sizeHint())
            self.listWidget.setItemWidget(item, custom_widget)
            self.listWidget.addItem(item)
            problemNum = problemNum + 1

        global nowpos
        nowpos = 0
        global questionBrowser
        questionBrowser = self.questionBrowser
        self.questionBrowser.append(self.result[nowpos][1])

        self.conn = sqlite3.connect('test1.db')
        self.cur = self.conn.cursor()
        sql = "SELECT * FROM Exam WHERE eid = '" + eid + "'"
        self.cur.execute(sql)
        mytime = self.cur.fetchall()

        endT = mytime[0][4].replace("오전", "AM")
        endT = endT.replace("오후", "PM")

        startT = mytime[0][3].replace("오전", "AM")
        startT = startT.replace("오후", "PM")

        aaa = datetime.strptime(startT, "%p %I:%M:%S")
        bbb = datetime.strptime(endT, "%p %I:%M:%S")

        testtime = bbb - aaa
        # currentTime = testtime.strftime("%-H:%M:%S")
        # print(currentTime)
        self.timer.setDigitCount(8)
        self.timer.display(str(testtime))

        self.pre_btn.clicked.connect(self.pre)
        self.next_btn.clicked.connect(self.next)
        self.submit_btn.clicked.connect(self.submit)

    def pre(self):
        print("이전")
        global nowpos
        if nowpos > 0:
            nowpos = nowpos - 1
            self.questionBrowser.setText(self.result[nowpos][1])
        else:
            QMessageBox.about(self, "알림", "첫 문제")

    def next(self):

        print("다음")
        global nowpos
        if nowpos < len(self.result) - 1:
            nowpos = nowpos + 1
            self.questionBrowser.setText(self.result[nowpos][1])
        else:
            QMessageBox.about(self, "알림", "마지막 문제")

    def submit(self):
        print("제출")
        self.hide()


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def thread_send_webcam(server_socket, args):
    print("USER : CANDIDATE")
    cheatDetector = CheatDetector(args)
    capture = cv2.VideoCapture(0)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    while True:
        ret, frame = capture.read()

        if ret == False:
            continue

        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        imgData = np.array(imgencode).tobytes()

        cheat_info = cheatDetector.process(frame)  # Cheat info: 0 Normal 1 CheatLeft 2 NoFace 3 CheatRight
        cheatData = bytes([cheat_info])

        stringData = imgData + cheatData  # 이미지 데이터 뒤에 치트 정보 숫자 하나 꼽사리 끼겠습니다

        try:

            server_socket.send('1'.encode(encoding='ISO-8859-1'))
            server_socket.send(str(len(stringData)).ljust(16).encode(encoding='ISO-8859-1'))
            server_socket.send(stringData)
            server_socket.recv(1).decode(encoding='ISO-8859-1')

        except ConnectionResetError as e:
            break

        except ConnectionAbortedError as e:
            break

        # cv2.imshow('client', frame)

    server_socket.close()


def thread_receive_webcam(server_socket):
    print("USER : SUPERVISOR")

    while True:
        try:
            uid = server_socket.recv(1024).decode(encoding='ISO-8859-1')

            if not uid:
                break

            length = server_socket.recv(16).decode(encoding='ISO-8859-1')
            print('length : ', length)

            stringData = recvall(server_socket, int(length))  # stringData = imgData + cheatData
            server_socket.send('1'.encode(encoding='ISO-8859-1'))

            imgData, cheatData = stringData[:-1], stringData[-1]
            data = np.frombuffer(imgData, dtype='uint8')
            decimg = cv2.imdecode(data, 1)
            decimg = cv2.flip(decimg, 1)
            cheat_info = int(cheatData)  # Cheat info: 0 Normal 1 Cheat 2 NoFace

            if True:  # DEBUG
                if cheat_info == 1:
                    cv2.putText(decimg, 'CHEAT : Upper Left', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif cheat_info == 2:
                    cv2.putText(decimg, 'CHEAT : Lower Left', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif cheat_info == 3:
                    cv2.putText(decimg, 'CHEAT : Upper Right', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif cheat_info == 4:
                    cv2.putText(decimg, 'CHEAT : Lower Right', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif cheat_info == 5:
                    cv2.putText(decimg, 'No Face', (decimg.shape[1] // 4, decimg.shape[0] // 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            window_name = str(uid)
            x = int(re.findall("\d+", window_name)[-1])
            cv2.namedWindow(window_name)
            cv2.moveWindow(window_name, x, 100)
            cv2.imshow(window_name, decimg)

            key = cv2.waitKey(1)
            if key == ord('q'):  # press q to exit
                break

        except ConnectionAbortedError as e:
            break


class thread_socket_GUI(QThread):
    # parent = MainWidget을 상속 받음.

    socket = None
    str = None
    result_queue = None

    def __init__(self, parent, socket, str, result_queue):
        super().__init__(parent)
        self.socket = socket
        self.str = str
        self.result_queue = result_queue

    def run(self):
        self.socket.send(self.str.encode(encoding='ISO-8859-1'))
        result = self.socket.recv(1024).decode(encoding='ISO-8859-1')
        print("recv:", result)

        if self.result_queue is not None:
            self.result_queue.append(result)
            print(self.result_queue)
        else:
            print("result_queue is none")


# 메인창
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # socket connection
    # host = '192.168.219.100'
    host = '100.26.161.192'
    port = 7777
    is_supervisor = False

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, port))

    w_login = Login()
    w_login.show()

    sys.exit(app.exec_())
