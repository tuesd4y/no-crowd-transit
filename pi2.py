import time

from abstractPi import AbstractRaspberryPi
from communication.messages import MovementUpdate
from people_counter.peopleCounter import PeopleTracker
from sensors.cameraSensor import CameraSensor
from sensors.distanceSensor import DistanceSensor
from sensors.gyroSensor import GyroSensor


class RaspberryPi2(AbstractRaspberryPi):
    cs: CameraSensor

    def __init__(self):
        self.activeSensors = {}
        self.initialSensors = {"gyro": GyroSensor, "camera": CameraSensor,
                               "distance": DistanceSensor}
        self.sensorCnt = 0
        AbstractRaspberryPi.__init__(self, "pi2", 5556, 5555)

        self.camera_start_time = time.time()
        self.cs = self.activeSensors['camera']

        self.regularDistance = 100

        self.peopleCounter = PeopleTracker()
        # if you want to write a debug video (into 'out_video.mp4') set this to true
        # self.peopleCounter.writeVideo = True
        self.peopleCounter.setup()

        # Subscribe to frames of the cameraSensor and delegate
        self.cs.subject.subscribe(on_next=self.on_img_received,
                                  on_completed=self.on_last_image,
                                  on_error=lambda err: print("errored"))
        self.peopleCounter.subject.subscribe(on_next=self.on_people_moved)

    def on_people_moved(self, movement):
        """
        React on a detected movement from the [PeopleTracker]. This can be for instance a group of two people walking
        over the camera fieldOfView midway line and therefore into the stop.
        :param movement: (people moving into the stop, people moving out of the stop)
        :return: nothing
        """
        up, down = movement
        print(f"Camera detected movement! ->  to stop: {down}, from stop: {up}, now validating")

        # Check if distance sensor validates the movement.
        # If measured distance is less than expected, then somebody is currently moving through the "measurement line"
        # of the distance sensor, thus our camera movement is validated and gets sent by message
        # Otherwise we can ignore the action without any additional handling.
        current_distance = self.activeSensors['distance'].get_distance()
        print(f"current_distance: {current_distance}")

        if current_distance < self.regularDistance:
            self.send_message(MovementUpdate(up, down))
            print("sent message to pi1")
        else:
            print("Distance sensor invalidated peopleTracker data!")

    def on_img_received(self, frame):
        """
        Delegate the received image to the peopleCounter analyzer
        :param frame:
        :return:
        """
        self.peopleCounter.analyze_frame(frame)

    def on_last_image(self):
        """
        Stop the peopleCounter when the last frame of the video (or camera) was receivd
        :return:
        """
        self.peopleCounter.tear_down()

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
