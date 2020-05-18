import time

from abstractPi import AbstractRaspberryPi
from communication.messages import CameraSensorUpdate
from sensors.display import Display
from sensors.gesture import GestureSensor


class RaspberryPi1(AbstractRaspberryPi):
    def __init__(self):
        self.activeSensors = {}
        self.initialSensors = {"gesture": GestureSensor, "display": Display}
        self.sensorCnt = 0
        AbstractRaspberryPi.__init__(self, "pi1", 5555, 5556)

    def set_window_location(self, x, y):
        self.move(x, y)

    def sampling_thread(self):
        time.sleep(5)
        while True:
            if self.activeSensors["gesture"].get_gesture() == "Up":
                response = self.send_message("p1 request orientation")
                if "orientation" in str(response):
                    self.activeSensors["display"].on(str(response))

    def on_receive_object(self, res):
        if type(res) == CameraSensorUpdate:
            self.respond("ok")
            self.activeSensors["display"].on(res.peopleWalkingFromStop)
