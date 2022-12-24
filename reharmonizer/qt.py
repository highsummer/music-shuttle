import sys

from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt


class Form(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        Sheet(self)


class Draggable(QWidget):
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos


class Key(QLabel, Draggable):
    def __init__(self, *args, **kwargs):
        Draggable.__init__(self, *args, **kwargs)
        self.setStyleSheet('background-color: orange')


class Sheet(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        keys = []
        key_height = 5
        unit_width = 20

        key = Key(self)
        key.setGeometry(0, 0, 100, 100)

        # for key in song.sing():
        #     if key.note is None:
        #         continue
        #     w = QWidget(self)
        #     w.setGeometry(key.start * unit_width, key.note.midi_number() * key_height, key.length * unit_width, key_height)
        #     w.setStyleSheet('background-color: red')
        
        self.init_widget()

    def init_widget(self):
        self.setWindowTitle("Hello World")
        self.setGeometry(0, 0, 640, 480)
        # self.setMouseTracking(True)
    
    def moveEvent(self, QMoveEvent):
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    exit(app.exec_())