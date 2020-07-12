import pyfakewebcam
from globals import WIDTH, HEIGHT

# load fake camera device
# type these into terminal first
# sudo modprobe -r v4l2loopback
# sudo modprobe v4l2loopback devices=1 video_nr=20 card_label="v4l2loopback" exclusive_caps=1
# when using zoom, select "v4l2loopback" as the video input

# setup fake camera
camera = pyfakewebcam.FakeWebcam("/dev/video20", WIDTH, HEIGHT)
