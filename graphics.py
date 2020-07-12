import os
import cv2
import requests
import pyfakewebcam
import numpy as np
import copy

from PIL import ImageGrab

from globals import WIDTH, HEIGHT


def get_mask(frame, bodypix_url="http://localhost:9000/mask-frame"):
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


def overlay_screen(frame):
    overlaid = copy.deepcopy(frame)
    screen = ImageGrab.grab(bbox=(0, 200, 400, 440))
    screen_np = np.array(screen)
    screen_img = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)
    overlaid[0:240, 0:400] = screen_img

    return overlaid


def remove_background(cap, background_scaled, frame, screen_is_visible):
    # fetch the mask with retries (the app needs to warmup and we're lazy)
    # e v e n t u a l l y c o n s i s t e n t

    print(screen_is_visible)
    background = (
        overlay_screen(background_scaled) if screen_is_visible else background_scaled
    )

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

