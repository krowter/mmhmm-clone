import os
import cv2
import requests
import pyfakewebcam
import numpy as np
import copy
from dotenv import load_dotenv
load_dotenv()

from PIL import ImageGrab

from globals import WIDTH, HEIGHT

PORT = os.getenv("PORT")

# 
# Source for get_mask, post_process_mask, and remove_background function
# https://elder.dev/posts/open-source-virtual-background/
# license: https://creativecommons.org/licenses/by/4.0/
# changes made to original code:
# - add conditionals based on states


def get_mask(frame, bodypix_url=f"http://localhost:{PORT}/mask-frame"):
    _, data = cv2.imencode(".jpg", frame)
    r = requests.post(
        url=bodypix_url,
        data=data.tobytes(),
        headers={"Content-Type": "application/octet-stream"},
    )

    mask = np.frombuffer(r.content, dtype=np.uint8)
    mask = mask.reshape((frame.shape[0], frame.shape[1]))
    return mask


def post_process_mask(mask):
    mask = cv2.dilate(mask, np.ones((10, 10), np.uint8), iterations=1)
    mask = cv2.blur(mask.astype(float), (30, 30))
    return mask


def shift_image(img, dx, dy):
    img = np.roll(img, dy, axis=0)
    img = np.roll(img, dx, axis=1)
    if dy > 0:
        img[:dy, :] = 0
    elif dy < 0:
        img[dy:, :] = 0
    if dx > 0:
        img[:, :dx] = 0
    elif dx < 0:
        img[:, dx:] = 0
    return img


def overlay_screen(frame, presenter_large):
    overlaid = copy.deepcopy(frame)
    (width, height) = (400, 440) if presenter_large else (600, 640)
    screen = ImageGrab.grab(bbox=(0, 200, width, height))
    screen_np = np.array(screen)
    screen_img = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)
    overlaid[0 : height - 200, 0:width] = screen_img

    return overlaid


def remove_background(cap, background_scaled, frame, state):
    if not state["virtual_background"]:
        return (
            overlay_screen(frame, state["presenter_large"])
            if state["screen_is_visible"]
            else frame
        )

    background = (
        overlay_screen(background_scaled, state["presenter_large"])
        if state["screen_is_visible"]
        else background_scaled
    )

    if not state["presenter_large"]:
        small_frame = cv2.resize(copy.deepcopy(frame), (320, 240))
        frame = np.ones((HEIGHT, WIDTH, 3), dtype="uint8")
        frame[240:480, 320:640] = small_frame

    mask = None
    while mask is None:
        try:
            mask = get_mask(frame)
        except requests.RequestException:
            print("mask request failed, retrying")

    # post-process mask and frame
    mask = post_process_mask(mask)

    # composite the foreground and background
    inv_mask = 1 - mask
    for c in range(frame.shape[2]):
        frame[:, :, c] = frame[:, :, c] * mask + background[:, :, c] * inv_mask

    return frame

