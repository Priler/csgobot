import csv
import random
import time
import sys
from pathlib import Path
from math import *
from ctypes import *
from concurrent.futures import ThreadPoolExecutor

from uutils.controls.mouse.pyautogui import MouseControls

u32 = windll.user32
tp = ThreadPoolExecutor(1)
mouse = MouseControls()

def threaded(fn):
    def wrapper(*args, **kwargs):
        return tp.submit(fn, *args, **kwargs)  # returns Future object

    return wrapper


class Locker(object):
    def __init__(self, args, screen, head_list):
        self.alive = True

        self.top_x = screen[0]
        self.top_y = screen[1]
        self.len_x = screen[2]
        self.len_y = screen[3]

        self.mouse_in_box = False
        self.lock_sen = args["mouse_sen"]
        self.head_first = args["head_first"]
        self.lock_smooth = args["mouse_smooth"]
        self.semi_delay = args["semi_delay"]

        self.recoil_mode = False
        self.fire_mode = False
        self.lock_mode = True
        self.left_pressed = False

        self.recoil_k = args["recoil_sen"]
        self.bbox = None
        self.second_bbox = None
        self.shot_time = 0
        self.weapon_mode = 0

        self.head_list = head_list

        self.recoil = []
        self.__get_recoil_path()
        self.check_fire()

    def __del__(self):
        tp.shutdown(wait=True)
    
    def __get_near_bbox(self, bbox_list, position):
        dist_list = []

        for det in bbox_list:
                _, x_c, y_c, _, _ = det
                dist = (self.len_x * float(x_c) + self.top_x - position[0]) ** 2 + (
                        self.len_y * float(y_c) + self.top_y - position[1]) ** 2
                dist_list.append(dist)

        det = bbox_list[dist_list.index(min(dist_list))]

        tag, x_center, y_center, width, height = det
        x_center, width = self.len_x * float(x_center) + self.top_x, self.len_x * float(width)
        y_center, height = self.len_y * float(y_center) + self.top_y, self.len_y * float(height)

        if tag not in self.head_list:
            y_center -= height // 2.5

        return(x_center, y_center, width, height, int(tag))

    def lock(self, aims):
        # mouse_pos_x, mouse_pos_y = self.top_x + self.len_x // 2, self.top_y + self.len_y // 2
        mouse_pos_x, mouse_pos_y = mouse.get_position()

        if len(aims):
            body_list = [x for x in aims if int(x[0]) not in self.head_list]
            aims = [x for x in aims if int(x[0]) in self.head_list]

            if not len(aims) and not len(body_list):
                return

            x_center, y_center, width, height, tag = self.__get_near_bbox(aims if len(aims) else body_list, (mouse_pos_x, mouse_pos_y))

            theta_x = atan((mouse_pos_x - x_center) / 640) * 180 / pi
            theta_y = atan((mouse_pos_y - y_center) / 640) * 180 / pi

            x = (theta_x / self.lock_sen) / 0.022
            y = (theta_y / self.lock_sen) / 0.03
            
            self.bbox = (x_center - (width // 2), x_center + (width // 2), y_center - (height // 2), y_center + (height // 2))

            if tag in self.head_list and len(body_list):
                x_center, y_center, width, height, tag = self.__get_near_bbox(body_list, (x_center, y_center))
                self.second_bbox = (x_center - (width // 3), x_center + (width // 3), y_center - (height // 3), y_center + (height // 3))
            else:
                self.second_bbox = None

            self.check_box()

            if self.lock_mode:
                if self.lock_smooth > 1.00:
                    rel_x = 0.
                    rel_y = 0.
                    if rel_x > x:
                        rel_x += 1. + (x / self.lock_smooth)
                    elif rel_y < x:
                        rel_x -= 1. - (x / self.lock_smooth)
                    if rel_y > y:
                        rel_y += 1. + (y / self.lock_smooth)
                    elif rel_y < y:
                        rel_y -= 1. - (y / self.lock_smooth)
                else:
                    rel_x = x
                    rel_y = y

                recoil_x, recoil_y = 0., 0.
                if self.recoil_mode and self.left_pressed:
                    t = time.time()
                    sum_t = 0
                    for i in self.recoil:
                        if t - self.shot_time > sum_t / 1000:
                            sum_t += i[2]
                            recoil_x += i[0]
                            recoil_y += i[1]
                        else:
                            break

                if not self.mouse_in_box:
                    u32.mouse_event(0x0001,
                                    int(-rel_x / self.lock_smooth + recoil_x * self.recoil_k),
                                    int(-rel_y / self.lock_smooth - recoil_y * self.recoil_k), 0, 0)

                else: self.recoil_only()
            elif self.recoil_mode:
                self.recoil_only()

    @threaded
    def check_fire(self):
        while self.alive:
            if self.fire_mode and self.mouse_in_box:
                if self.weapon_mode == 0:
                    step_time = random.uniform(.2, .3) / 10

                    u32.mouse_event(0x0002, 0, 0, 0, 0)

                    for i in range(10):
                        self.check_box()

                        if not self.mouse_in_box:
                            break
                        time.sleep(step_time)

                        self.check_box()

                    u32.mouse_event(0x0004, 0, 0, 0, 0)

                if self.weapon_mode == 1:
                    u32.mouse_event(0x0008 + 0x0010, 0, 0, 0, 0)
                    time.sleep(.15)
                    u32.mouse_event(0x0002 + 0x0004, 0, 0, 0, 0)
                    time.sleep(.1)
                    u32.mouse_event(0x0008 + 0x0010, 0, 0, 0, 0)

                if self.weapon_mode == 2:
                    u32.mouse_event(0x0002 + 0x0004, 0, 0, 0, 0)
                    time.sleep(self.semi_delay)

            time.sleep(3 / 1000)

    def recoil_only(self):
        if self.recoil_mode and self.left_pressed:
            recoil_x, recoil_y = 0., 0.
            t = time.time()
            sum_t = 0
            for i in self.recoil:
                if t - self.shot_time > sum_t / 1000:
                    sum_t += i[2]
                    recoil_x = i[0]
                    recoil_y = i[1]
                else:
                    u32.mouse_event(0x0001,
                                    int(recoil_x * self.recoil_k),
                                    int(-recoil_y * self.recoil_k), 0, 0)
                    break

    def __get_recoil_path(self):
        if getattr(sys, 'frozen', False):
            p = Path(sys.executable).parents[0]
        elif __file__:
            p = Path(__file__).parents[1]

        csv_path = str(p) + "/cs/recoil.csv"

        for i in csv.reader(open(csv_path, encoding='utf-8-sig')):
            self.recoil.append([float(x) for x in i])

    def reset(self):
        self.bbox = None
        self.second_bbox = None
        self.mouse_in_box = False

    def check_box(self):
        # mouse_pos_x, mouse_pos_y = self.top_x + self.len_x // 2, self.top_y + self.len_y // 2
        mouse_pos_x, mouse_pos_y = mouse.get_position()

        if self.bbox is not None:
            self.mouse_in_box = self.bbox[0] <= mouse_pos_x <= self.bbox[1] and self.bbox[2] <= mouse_pos_y <= self.bbox[3]
        
        if self.mouse_in_box == False and self.second_bbox is not None and self.bbox == None:
            self.mouse_in_box = self.second_bbox[0] <= mouse_pos_x <= self.second_bbox[1] and self.second_bbox[2] <= mouse_pos_y <= self.second_bbox[3]
