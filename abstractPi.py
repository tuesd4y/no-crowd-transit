import threading

import zmq
from PyQt5 import QtWidgets, uic

from communication.abstractReceiver import AbstractReceiver
from communication.abstractSender import AbstractSender


class AbstractRaspberryPi(QtWidgets.QMainWindow):
    def __init__(self, name, s_port, r_port):
        self.name = name
        self.sensorCnt = 0
        self.s_port = s_port
        self.r_port = r_port
        super(AbstractRaspberryPi, self).__init__()
        uic.loadUi('ui/pi.ui', self)

        self.setWindowTitle(name)
        self.sensorListWidget = self.findChild(QtWidgets.QListWidget, 'lSensors')

        # communication
        self.sender = AbstractSender(self.s_port)
        self.receiver = AbstractReceiver(self.r_port)
        self.lock = threading.Lock()
        threading.Thread(target=self.receiver_thread).start()

        # start sampling
        threading.Thread(target=self.sampling_thread).start()

        for s in self.initialSensors:
            self.add_sensor(self.initialSensors[s], s)

        self.show()

    def add_sensor(self, type, name):
        if name == "" or name is None:
            name = type + str(self.sensorCnt)
        self.activeSensors[name] = type()
        self.activeSensors[name].set_name(self.name + " " + name)
        self.sensorListWidget.addItem(name)
        self.sensorCnt += 1

    def send_message(self, message):
        """
        Send a message to zmq and return the response (blocking)
        :param message: to send
        :return: the response
        """
        self.lock.acquire()
        self.sender.socket.send_string(message)
        response = self.sender.socket.recv()
        self.lock.release()
        return response

    def on_receive_string(self, message):
        """
        Callback for when a new string is received
        :param message: the received string
        :return: nothing
        """
        pass

    def on_receive_object(self, res):
        """
        Callback for when a new object is received
        :param message: the received string
        :return: nothing
        """
        pass

    def receive_message(self):
        """
        Gets executed periodically by the receiver thread.
        If a request is received from the zeroMQ protocol, the on_receive_object() or on_receive_string() method will
        be executed, respectively.
        """
        results = self.receiver.poller.poll(10)
        for (socket, count) in results:
            if socket == self.receiver.socket and count > 0:
                res = self.receiver.socket.recv()
                if res is str:
                    self.on_receive_string(res)
                else:
                    self.on_receive_object(res)

    def receiver_thread(self):
        while True:
            self.receive_message()
