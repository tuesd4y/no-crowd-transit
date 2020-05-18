import multiprocessing
import statistics
import time

import numpy as np
from rx.scheduler import ThreadPoolScheduler

from abstractPi import AbstractRaspberryPi
from communication.messages import CameraSensorUpdate
from sensors.cameraSensor import CameraSensor
from sensors.distanceSensor import DistanceSensor
from sensors.gyroSensor import GyroSensor
from rx import operators as op


class RaspberryPi2(AbstractRaspberryPi):
    cs: CameraSensor

    def __init__(self):
        self.activeSensors = {}
        self.initialSensors = {"gyro": GyroSensor, "camera": CameraSensor,
                               "distance": DistanceSensor}
        self.sensorCnt = 0
        AbstractRaspberryPi.__init__(self, "pi2", 5556, 5555)

        person_count = 0
        self.camera_start_time = time.time()
        self.cs = self.activeSensors['camera']

        self.towardsStop = 0

        optimal_thread_count = multiprocessing.cpu_count()
        pool_scheduler = ThreadPoolScheduler(optimal_thread_count)

        # read image from rx stream here
        self.cs.subject.pipe(
            op.map(lambda img: np.mean(img)),
            op.buffer_with_count(20),
            op.map(lambda l: statistics.mean(l))
        ).subscribe(on_next=self.on_img_received,
                    on_completed=lambda: print("completed"),
                    on_error=lambda err: print("errored"),
                    scheduler=pool_scheduler)

    def on_img_received(self, avg: float):
        # check if screen is black (average pixel < 120)
        if avg < 120:
            self.towardsStop += 1
            res = self.send_message(CameraSensorUpdate(0, self.towardsStop))


    def set_window_location(self, x, y):
        self.move(x, y)

    def on_receive_object(self, res):
        if "orientation" in str(res):
            self.receiver.socket.send_string("p2 sends orientation" + str(self.activeSensors["gyro"].get_orientation()))

    def sampling_thread(self):
        time.sleep(5)
        while True:
            pass
            # Do some sampling
