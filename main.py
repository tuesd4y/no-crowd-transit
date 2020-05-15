import sys
from PyQt5 import QtWidgets, uic
from pi1 import RaspberryPi1
from pi2 import RaspberryPi2


class Main(QtWidgets.QMainWindow):
    def __init__(self):
        self.sensorCnt = 0
        super(Main, self).__init__()
        uic.loadUi('ui/main.ui', self)

        self.pi1 = RaspberryPi1()
        self.pi2 = RaspberryPi2()

        self.setWindowTitle("Connected Raspberry Pis")
        self.piListWidget = self.findChild(QtWidgets.QListWidget, 'lPis')
        self.piListWidget.addItem("pi1")
        self.piListWidget.addItem("pi2")
        self.show()

    def set_window_location(self, x, y):
        self.move(x,y)

app = QtWidgets.QApplication(sys.argv)
window = Main()
app.exec_()