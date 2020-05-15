import threading
import time

from abstractPi import AbstractRaspberryPi
from communication.abstractReceiver import AbstractReceiver
from communication.abstractSender import AbstractSender
from sensors.accelSensor import AccelSensor
from sensors.audio import Audio
from sensors.brightnessSensor import BrightnessSensor
from sensors.button import Button
from sensors.cameraSensor import CameraSensor
from sensors.display import Display
from sensors.distanceSensor import DistanceSensor
from sensors.gesture import GestureSensor
from sensors.greenLED import GreenLED
from sensors.gyroSensor import GyroSensor
from sensors.humiditySensor import HumiditySensor
from sensors.infraredSensor import InfraredSensor
from sensors.microphone import MicrophoneSensor
from sensors.redLED import RedLED
from sensors.rfidSensor import RFIDSensor
from sensors.servo import Servo
from sensors.tempSensor import TempSensor
from sensors.weightSensor import WeightSensor


class RaspberryPi2(AbstractRaspberryPi):
    def __init__(self):
        self.activeSensors = {}
        self.initialSensors = {"gyro": GyroSensor}
        self.sensorCnt = 0
        AbstractRaspberryPi.__init__(self, "pi2", 5556, 5555)

        for s in self.initialSensors:
            self.add_sensor(self.initialSensors[s], s)

        self.show()

        # communication
        self.sender = AbstractSender(self.s_port)
        self.receiver = AbstractReceiver(self.r_port)
        self.lock = threading.Lock()
        threading.Thread(target=self.receiver_thread).start()

        # start sampling
        threading.Thread(target=self.sampling_thread).start()

    def set_window_location(self, x, y):
        self.move(x,y)

    def receiver_thread(self):
        while True:
            incoming_request = self.receiver.socket.recv()
            if "orientation" in str(incoming_request):
                self.receiver.socket.send_string("p2 sends orientation"+str(self.activeSensors["gyro"].get_orientation()))

    def send_message(self, message):
        self.lock.acquire()
        self.sender.socket.send_string(message)
        response = self.sender.socket.recv()
        self.lock.release()

    def sampling_thread(self):
        time.sleep(5)
        while True:
            None
            # Do some sampling
