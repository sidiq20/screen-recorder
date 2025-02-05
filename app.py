import sys, time, threading, subprocess, wave
import numpy as np
import cv2
import mss
import pyaudio

from PyQt5 import QtCore, Qtgui, QtWidgets

class ScreenRecorderThread(QtCore.QThread):
    frameCaptured = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, monitor=None):
        super().__init__()
        self.running = True
        self.sct = mss.mss()

        self.monitor = monitor if monitor is not None else self.sct.monitors[1]

    def run(self):
        while self.running:
            sct_img = self.sct.grab(self.monitor)
            frame = np.array(sct_img)
            # Convert from BGRA to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            self.frameCaptured.emit(frame)
            time.sleep(1/30) #target ¬30 fps

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class WebcamThread(QtCore.QThread):
    frameCaptured = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.cap = cv2.VideoCapture(Self.camera_index)

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frameCaptured.emit(frame)
            time.sleep(1/30) # Approx. 30fps

    def stop(self):
        self.running = False
        self.cap.release()
        self.quit()
        self.wait()


class AudioRecorder:
    def __init__(self, filename="temp_audio.wav", rate=44100, channels=2, frames_per_buffer=1024):
        self.filename = filename
        self.rate = rate
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.format = pyaudio.paInt16
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.frames_per_buffer)
        self.frames = []
        self.running = True

    def record(self):
        while self.running:
            try:
                data = self.stream.read(self.frames_per_buffer)
                self.frames.append(data)
            except Exception as e:
                print("Audio error:", e)
        # When finished, save audio file.
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class DraggableLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.dragging = False
        self.offset = QtCore.QPoint()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            newPos = self.mapToParent(event.pos() - self.offset)
            self.move(newPos)

    def mouseReleaseEvent(self, event):
        self.dragging = False

class Recorder(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Recorder with Webcam Overlay")

        self.setGeometry(100, 100, 1280, 720)

        self.labelDisplay = QtWidgets.QLabel(self)
        self.labelDisplay.setGeometry(0, 0, 1280, 720)
        self.labelDisplay.setScaledContents(True)

        self.webcamLabel = DraggableLabel(self)
        self.webcamLabel.setGeometry(50, 50, 320, 240)
        self.webcamLabel.setStyle("border: 2px solid red;")

        self.screenFrame = None
        self.webcamFrame = None

        self.videoWriter = cv2.VideoWriter("output.avi" ,
                                           cv2.videoWriter_fourcc(*"MJPG"),
                                           30,
                                           (1280, 720))

        self.screenThread = ScreenRecorderThread()
        self.screenThread.frameCaptured.connect(self.updateScreen)
        self.screenThread.start()

        self.webcamThread = WebcamThread()
        self.screenThread.frameCaptured.connect(self.updatedScreen)
        self.screenThread.start()

        self.audioRecorder = AudioRecorder("temp_audio.wav")
        self.audioRecorder = threading

#main entry point
if __name__ == "__main__":
    app = QtWidgets.QApplications(sys.argv)
    recorder = Recorder()
    recorder.show()
    sys.exit(app.exec_())