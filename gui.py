import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QPushButton
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap

from fakeCam import camera
from graphics import remove_background

from globals import WIDTH, HEIGHT

screen_is_visible = False
background = cv2.imread("assets/background.jpg")
background_scaled = cv2.resize(background, (WIDTH, HEIGHT))


class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        global screen_is_visible
        cap = cv2.VideoCapture("/dev/video0")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 60)

        while True:
            ret, frame = cap.read()

            if ret:
                print(screen_is_visible)
                # remove background
                cropped = remove_background(
                    cap, background_scaled, frame, screen_is_visible
                )

                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # channel to video output device
                camera.schedule_frame(rgbImage)

                # https://stackoverflow.com/a/55468544/6622587
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(
                    rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
                )
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def on_click(self):
        global screen_is_visible
        screen_is_visible = not screen_is_visible

    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def initUI(self):
        self.resize(WIDTH + 80, HEIGHT)
        self.label = QLabel(self)
        self.label.resize(WIDTH, HEIGHT)

        button = QPushButton("PyQt5 button", self)
        button.setToolTip("This is an example button")
        button.move(WIDTH, 0)
        button.clicked.connect(self.on_click)

        th = Thread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        self.show()

