class CameraSensorUpdate():
    def __init__(self, peopleWalkingTowardsStop, peopleWalkingFromStop):
        self.peopleWalkingTowardsStop = peopleWalkingTowardsStop
        self.peopleWalkingFromStop = peopleWalkingFromStop


class DistanceSensorUpdate():
    def __init__(self, distance):
        self.distance = distance
