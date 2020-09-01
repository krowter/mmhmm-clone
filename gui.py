import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QPushButton
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap

from fakeCam import camera
from graphics import remove_background

from globals import WIDTH, HEIGHT

state = {
    "virtual_background": True,
    "screen_is_visible": False,
    "presenter_large": False,
}

background = cv2.imread("assets/sebastian-kurpiel-R7qWs39obtk-unsplash.jpg")
background_scaled = cv2.resize(background, (WIDTH, HEIGHT))

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        global state
        cap = cv2.VideoCapture("/dev/video0")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 60)

        while True:
            ret, frame = cap.read()

            if ret:
                # remove background
                cropped = remove_background(cap, background_scaled, frame, state)

                rgbImage = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)

                # channel to video output device
                camera.schedule_frame(rgbImage)

                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(
                    rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888
                )
                p = convertToQtFormat.scaled(WIDTH, HEIGHT, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setFixedSize(self.size())

    def toggle_virtual_background(self):
        global state
        state["virtual_background"] = not state["virtual_background"]

    def toggle_screen(self):
        global state
        state["screen_is_visible"] = not state["screen_is_visible"]

    def toggle_layout(self):
        global state
        state["presenter_large"] = not state["presenter_large"]

    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def initUI(self):
        self.resize(WIDTH + 120, HEIGHT)
        self.label = QLabel(self)
        self.label.resize(WIDTH, HEIGHT)

        toggle_screen = QPushButton("Screen", self)
        toggle_screen.setGeometry(WIDTH, 0, 120, 50)
        toggle_screen.clicked.connect(self.toggle_screen)

        toggle_layout = QPushButton("Layout", self)
        toggle_layout.setGeometry(WIDTH, 50, 120, 50)
        toggle_layout.clicked.connect(self.toggle_layout)

        toggle_layout = QPushButton("Background", self)
        toggle_layout.setGeometry(WIDTH, 100, 120, 50)
        toggle_layout.clicked.connect(self.toggle_virtual_background)

        th = Thread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        self.show()

