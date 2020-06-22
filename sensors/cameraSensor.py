import threading

from PyQt5 import uic, QtWidgets
import cv2
from PyQt5.QtWidgets import QLabel, QPushButton, QRadioButton
from rx.subject import Subject


class CameraSensor(QtWidgets.QMainWindow):

    def __init__(self):
        super(CameraSensor, self).__init__()
        self.subject = Subject()
        uic.loadUi('ui/camera.ui', self)
        self.rCamera = self.findChild(QRadioButton, 'rCamera')
        self.rCamera.setChecked(True)
        self.rCamera.toggled.connect(self.camera_mode)
        self.rVideo = self.findChild(QRadioButton, 'rVideo')
        self.bStart = self.findChild(QPushButton, 'bStart')
        self.rVideo.toggled.connect(self.video_mode)
        self.mode = "Camera"
        self.show()
        self.img = None
        self.liveView = True
        self.iCamImage = self.findChild(QLabel, 'iCam')
        self.viewButton = self.findChild(QPushButton, 'bLiveView')
        self.viewButton.clicked.connect(self.toggle_view)
        self.name = ""
        self.cam = None
        self.bStart.clicked.connect(self.start)
        self.running = False

        # set your video path here
        self.videoPath = "video_examples/example_3.mp4"

        # if you don't get a camera image change this to another index
        self.camIndex = 0

        # self.img_stream = defer()

    def set_window_location(self, x, y):
        self.move(x, y)

    def start(self):
        if not self.running:
            self.cam = cv2.VideoCapture(self.videoPath) if self.mode == "Video" else cv2.VideoCapture(self.camIndex)
            self.rCamera.setEnabled(False)
            self.rVideo.setEnabled(False)
            self.running = True
            threading.Thread(target=self.video_thread).start()
            self.bStart.setText("Stop")
        else:
            self.running = False
            self.rCamera.setEnabled(True)
            self.rVideo.setEnabled(True)
            self.bStart.setText("Start")

    def camera_mode(self):
        self.mode = "Camera"
        self.rVideo.setChecked(False)

    def video_mode(self):
        self.mode = "Video"
        self.rCamera.setChecked(False)

    def set_name(self, name):
        self.name = name
        self.setWindowTitle(name)

    def toggle_view(self):
        self.liveView = not self.liveView

    def get_image(self):
        return self.img

    def video_thread(self):
        cv2.startWindowThread()
        key = 0
        while self.running:
            # even though this is named camera, this might as well be the video source we're accessing here!
            ret, frame = self.cam.read()
            # self.img = frame
            if self.liveView and ret:
                # cv2.imwrite('/Users/dev/Downloads/test.png', self.img)
                cv2.imshow("Live Image " + self.name, frame)
                key = cv2.waitKey()
            if key & 0xFF == ord('q'):
                break

            if frame is None:
                break

            self.subject.on_next(frame)
            # publish image to rx stream here

        self.cam.release()
        # cv2.destroyAllWindows()
        self.cam = None
        self.subject.on_completed()
