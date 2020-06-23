# initialize the list of class labels MobileNet SSD was trained to
# detect
import cv2
import dlib
import imutils
import numpy as np
from imutils.video import FPS
from rx.subject import Subject

from people_counter.centroidtracker import CentroidTracker
from people_counter.trackableobject import TrackableObject


class PeopleTracker:
    def __init__(self):
        self.subject = Subject()
        self.writeVideo = False

    def setup(self):
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]

        # load our serialized model from disk
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe("people_counter/model/model.prototxt",
                                            "people_counter/model/model.caffemodel")
        # video_src = "video_examples/example_3.mp4"
        # self.vs = cv2.VideoCapture(video_src)

        # initialize the video writer (we'll instantiate later if need be)
        self.writer = None

        # initialize the frame dimensions (we'll set them as soon as we read
        # the first frame from the video)
        self.W = None
        self.H = None

        # instantiate our centroid tracker, then initialize a list to store
        # each of our dlib correlation trackers, followed by a dictionary to
        # map each unique object ID to a TrackableObject
        self.ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
        self.trackers = []
        self.trackableObjects = {}

        # initialize the total number of frames processed thus far, along
        # with the total number of objects that have moved either up or down
        self.totalFrames = 0
        self.totalDown = 0
        self.totalUp = 0

        # start the frames per second throughput estimator
        self.fps = FPS().start()

    def analyze_frame(self, frame):
        # resize the frame to have a maximum width of 500 pixels (the
        # less data we have, the faster we can process it), then convert
        # the frame from BGR to RGB for dlib
        frame = imutils.resize(frame, width=500)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # if the frame dimensions are empty, set them
        if self.W is None or self.H is None:
            (self.H, self.W) = frame.shape[:2]

        # if we are supposed to be writing a video to disk, initialize
        # the writer
        if self.writer is None and self.writeVideo:
            fourcc = cv2.VideoWriter_fourcc(*"MP4V")
            self.writer = cv2.VideoWriter("out_video.mp4", fourcc, 30,
                                          (self.W, self.H), True)

        # initialize the current status along with our list of bounding
        # box rectangles returned by either (1) our object detector or
        # (2) the correlation trackers
        self.status = "Waiting"
        rects = []

        # check to see if we should run a more computationally expensive
        # object detection method to aid our tracker
        # if totalFrames % args["skip_frames"] == 0:
        if self.totalFrames % 3 == 0:
            # set the status and initialize our new set of object trackers
            self.status = "Detecting"
            self.trackers = []

            # convert the frame to a blob and pass the blob through the
            # network and obtain the detections
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (self.W, self.H), 127.5)
            self.net.setInput(blob)
            detections = self.net.forward()

            # loop over the detections
            for i in np.arange(0, detections.shape[2]):
                # extract the confidence (i.e., probability) associated
                # with the prediction
                confidence = detections[0, 0, i, 2]

                # filter out weak detections by requiring a minimum
                # confidence
                if confidence > .5:
                    # extract the index of the class label from the
                    # detections list
                    idx = int(detections[0, 0, i, 1])

                    # if the class label is not a person, ignore it
                    if self.CLASSES[idx] != "person":
                        continue

                    # compute the (x, y)-coordinates of the bounding box
                    # for the object
                    box = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
                    (startX, startY, endX, endY) = box.astype("int")

                    # construct a dlib rectangle object from the bounding
                    # box coordinates and then start the dlib correlation
                    # tracker
                    tracker = dlib.correlation_tracker()
                    rect = dlib.rectangle(startX, startY, endX, endY)
                    tracker.start_track(rgb, rect)

                    # add the tracker to our list of trackers so we can
                    # utilize it during skip frames
                    self.trackers.append(tracker)

        # otherwise, we should utilize our object *trackers* rather than
        # object *detectors* to obtain a higher frame processing throughput
        else:
            # loop over the trackers
            for tracker in self.trackers:
                # set the status of our system to be 'tracking' rather
                # than 'waiting' or 'detecting'
                status = "Tracking"

                # update the tracker and grab the updated position
                tracker.update(rgb)
                pos = tracker.get_position()

                # unpack the position object
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())

                # add the bounding box coordinates to the rectangles list
                rects.append((startX, startY, endX, endY))

        # draw a horizontal line in the center of the frame -- once an
        # object crosses this line we will determine whether they were
        # moving 'up' or 'down'
        if self.writeVideo:
            cv2.line(frame, (0, self.H // 2), (self.W, self.H // 2), (0, 255, 255), 2)

        # use the centroid tracker to associate the (1) old object
        # centroids with (2) the newly computed object centroids
        objects = self.ct.update(rects)

        down = 0
        up = 0

        # loop over the tracked objects
        for (objectID, centroid) in objects.items():
            # check to see if a trackable object exists for the current
            # object ID
            to = self.trackableObjects.get(objectID, None)

            # if there is no existing trackable object, create one
            if to is None:
                to = TrackableObject(objectID, centroid)

            # otherwise, there is a trackable object so we can utilize it
            # to determine direction
            else:
                # the difference between the y-coordinate of the *current*
                # centroid and the mean of *previous* centroids will tell
                # us in which direction the object is moving (negative for
                # 'up' and positive for 'down')
                y = [c[1] for c in to.centroids]
                direction = centroid[1] - np.mean(y)
                to.centroids.append(centroid)

                # check to see if the object has been counted or not
                if not to.counted:
                    # if the direction is negative (indicating the object
                    # is moving up) AND the centroid is above the center
                    # line, count the object
                    if direction < 0 and centroid[1] < self.H // 2:
                        self.totalUp += 1
                        up += 1
                        to.counted = True

                    # if the direction is positive (indicating the object
                    # is moving down) AND the centroid is below the
                    # center line, count the object
                    elif direction > 0 and centroid[1] > self.H // 2:
                        self.totalDown += 1
                        down += 1
                        to.counted = True

            # store the trackable object in our dictionary
            self.trackableObjects[objectID] = to

            if self.writeVideo:
                # draw both the ID of the object and the centroid of the
                # object on the output frame
                text = "ID {}".format(objectID)
                cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

        if up != 0 or down != 0:
            self.subject.on_next((up, down))

        # construct a tuple of information we will be displaying on the
        # frame
        info = [
            ("Up", self.totalUp),
            ("Down", self.totalDown),
            ("Status", self.status),
        ]

        if self.writeVideo:
            # loop over the info tuples and draw them on our frame
            for (i, (k, v)) in enumerate(info):
                text = "{}: {}".format(k, v)
                cv2.putText(frame, text, (10, self.H - ((i * 20) + 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # check to see if we should write the frame to disk
        if self.writer is not None:
            self.writer.write(frame)

        # show the output frame
        # cv2.imshow("Frame", frame)
        # key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        # if key == ord("q"):
        #     break

        # increment the total number of frames processed thus far and
        # then update the FPS counter
        self.totalFrames += 1
        self.fps.update()
        # print("Total frames are {:d}".format(self.totalFrames))


    def tear_down(self):
        # stop the timer and display FPS information
        self.fps.stop()
        print("[INFO] elapsed time: {:.2f}".format(self.fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))

        # check to see if we need to release the video writer pointer
        if self.writer is not None:
            self.writer.release()

        # otherwise, release the video file pointer
        # else:
        #     self.vs.release()

        # close any open windows
        # cv2.destroyAllWindows()
