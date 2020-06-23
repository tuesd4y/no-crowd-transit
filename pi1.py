import time

from abstractPi import AbstractRaspberryPi
from communication.messages import MovementUpdate
from sensors.display import Display
from sensors.gesture import GestureSensor


class RaspberryPi1(AbstractRaspberryPi):
    def __init__(self):
        self.activeSensors = {}
        self.initialSensors = {"gesture": GestureSensor, "display": Display}
        self.sensorCnt = 0
        AbstractRaspberryPi.__init__(self, "pi1", 5555, 5556)

        self.current_people = 3
        self.activeSensors["display"].on(f"currently {self.current_people} at the stop.")

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
        """
        Handle objects received over the default communication channel
        :param res:
        :return:
        """
        if type(res) == MovementUpdate:
            self.respond("ok")

            # update number of people currently at the stop
            self.current_people -= res.peopleWalkingFromStop
            self.current_people += res.peopleWalkingTowardsStop

            print(f"p1 received to stop: {res.peopleWalkingTowardsStop}, from stop: {res.peopleWalkingFromStop}")

            # display a notification about the
            self.activeSensors["display"].on(f"currently {self.current_people} at the stop\nLast update: "
                                             f"(+{res.peopleWalkingTowardsStop}, -{res.peopleWalkingFromStop})")
