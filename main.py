import logging
import multiprocessing
from queue import Queue, Full, Empty
import sys, os

from configurator import config

from uutils.grabbers.obs_vc import Grabber
import cv2, math, time

from uutils.win32 import WinHelper
from uutils.fps import FPS
from uutils.cv2 import round_to_multiple
from uutils.time import sleep
import keyboard
from pygrabber.dshow_graph import FilterGraph

from cs.aim_lock_pi import Locker

from uutils.controls.mouse.pyautogui import MouseControls
from uutils.controls.mouse.win32 import MouseControls as MouseControlsWin32
from pynput import mouse as mouse_controller
import win32api, win32con, win32gui

from uutils.fov_mouse import FovMouseMovement

mouse = MouseControls() # for coordinates (windows DPI scaling compatible)
mouseWin32 = MouseControlsWin32() # for moving

# sensitivity = 2.1
# base_rel = 163_636 # 163_636

# print(f"Base rel is: {base_rel}")

# def test_hotkey_callback(triggered, hotkey):
#     mouseWin32.move_relative(int(base_rel), 0)

# def increase_hotkey_callback(triggered, hotkey):
#     global base_rel
#     base_rel += 1
#     print(f"Base rel increased: {base_rel}")

# def decrease_hotkey_callback(triggered, hotkey):
#     global base_rel
#     base_rel -= 1
#     print(f"Base rel decreased: {base_rel}")

# keyboard.add_hotkey(58, test_hotkey_callback, args=('triggered', 'hotkey'))
# keyboard.add_hotkey("f1", increase_hotkey_callback, args=('triggered', 'hotkey'))
# keyboard.add_hotkey("f2", decrease_hotkey_callback, args=('triggered', 'hotkey'))
# while True:
#     pass
# sys.exit(1)



# for listening for mouse clicks
# listener = mouse_controller.Listener(on_click=on_click)
# listener.start()

# PROCESS_PER_MONITOR_DPI_AWARE = 2
# ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

# logging
logging.basicConfig(level=logging.INFO & logging.DEBUG)

# read config
if not config:
    logging.error("Errors while parsing config file. Exiting.")
    exit(1)

# import detector
if config["main"]["detector"] == "yolov8":
    from detector_yolov8 import Detector
elif config["main"]["detector"] == "yolov7":
    from detector_yolov7 import Detector


# set selected detector as main
if multiprocessing.current_process().name == "MainProcess":
    logging.debug(f'Detector is set to {config["main"]["detector"]}')

config["detector"] = config[config["main"]["detector"]]


# config
AUTO_SHOOT = False  # rather apply auto shoot or press button to shoot
SHOOT_HOTKEY = 58  # 58 = CAPS-LOCK
CHANGE_TEAM_HOTKEY = "ctrl+t"
shoot_conf = (0.8, 0.7)  # minimum required conf for detection to shoot (head, body)
min_assist_dist = 300 # minimum required distance of crosshair to target for mouse move (assist)
min_shoot_dist = 50 # minimum required distance of crosshair to target for mouse click (shoot)

team = "ct"  # initial team
t_classes = ("t", "th")
ct_classes = ("c", "ch")
heads_cls_list = (1, 3)

detect_threshold = 0.7
iou_threshold = 0.2


# vars
enemy_team = None
e_classes = None
hotkey_to_shoot_pressed = False


# defs
def id_enemy_classes():
    global team, e_classes, enemy_team

    if team == "ct":
        e_classes = t_classes
        enemy_team = "t"
    else:
        e_classes = ct_classes
        enemy_team = "ct"

    print(f"CURRENT TEAM: {team}")
    print(f"ENEMY TEAM: {enemy_team}")


def change_team_hotkey_callback(triggered, hotkey):
    global team, enemy_team

    if team == "t":
        team = "ct"
    else:
        team = "t"

    id_enemy_classes()


def shoot_hotkey_callback(triggered, hotkey):
    global hotkey_to_shoot_pressed
    hotkey_to_shoot_pressed = True
    print("!!! SHOOT !!!")


def convert_bbox_to_aims(bbox):
    aims = []
    for a in bbox:
        xyxy = a["xyxy"]
        line = (a["cls"], *xyxy)
        aim = ('%g ' * len(line)).rstrip() % line
        aim = aim.split(' ')
        aims.append(aim)

    return aims


def get_game_windows_rect():
    try:
        if(config['grabber']['width'] != 0):
            # custom rect
            game_window_rect = [config['grabber']['left'], config['grabber']['top'], config['grabber']['width'], config['grabber']['height']]

            # auto pos detection
            if(config['grabber']['left'] == 0):
                gwr = list(WinHelper.GetWindowRect(config["grabber"]["window_title"], (8, 30, 16, 39)))  # cut the borders
                game_window_rect[0] = gwr[0]
                game_window_rect[1] = gwr[1]
        else:
            # auto rect
            game_window_rect = list(WinHelper.GetWindowRect(config["grabber"]["window_title"], (8, 30, 16, 39)))  # cut the borders
    except Exception as e:
        logging.error(f'Cannot grab window rect with name "{config["grabber"]["window_title"]}"')
        logging.error(e)
        os._exit(1)

    return game_window_rect


def get_nearest_bbox(bbox_list, screen):
    closest = 1000000
    aim_bbox = None

    # position is always center of the game window
    position = (
        screen[2] / 2,
        screen[3] / 2
    )

    for bbox in bbox_list:
        x, y, xw, yh = bbox["xyxy"]
        mid_x = int(x+((xw-x)/2))
        mid_y = int(y+((yh-y)/2))

        dist = math.dist([position[0], position[1]], [mid_x, mid_y])

        if dist < closest:
            closest = dist
            aim_bbox = (bbox, (mid_x, mid_y))

    # if tag not in head_list:
    #     y_center -= height // 2.5

    return aim_bbox[0], aim_bbox[1], closest


def grab_process(q):
    logging.info("GRAB process started")

    grabber = Grabber()

    if(grabber.type == "obs_vc"):
        if(config["grabber"]["obs_vc_device_index"] != -1):
            # init device by given index
            grabber.obs_vc_init(config["grabber"]["obs_vc_device_index"])
        else:
            # init device by given name
            graph = FilterGraph()

            try:
                device = grabber.obs_vc_init(graph.get_input_devices().index(config["grabber"]["obs_vc_device_name"]))
            except ValueError as e:
                logging.error(f'Could not find OBS VC device with name "{config["grabber"]["obs_vc_device_name"]}"')
                logging.error(e)
                os._exit(1)

    game_window_rect = get_game_windows_rect()

    # assure that width & height of capture area is multiple of 32
    if not config["detector"]["resize_image_to_fit_multiply_of_32"] and (
            int(game_window_rect[2]) % 32 != 0 or int(game_window_rect[3]) % 32 != 0):
        print("Width and/or Height of capture area must be multiply of 32")
        print("Width is", int(game_window_rect[2]), ", closest multiple of 32 is",
              round_to_multiple(int(game_window_rect[2]), 32))
        print("Height is", int(game_window_rect[3]), ", closest multiple of 32 is",
              round_to_multiple(int(game_window_rect[3]), 32))

        game_window_rect[2] = round_to_multiple(int(game_window_rect[2]), 32)
        game_window_rect[3] = round_to_multiple(int(game_window_rect[3]), 32)
        print("Width & Height was updated accordingly")

    while True:
        img = grabber.get_image({"left": int(game_window_rect[0]), "top": int(game_window_rect[1]), "width": int(game_window_rect[2]), "height": int(game_window_rect[3])})

        if img is None:
            continue

        # force only 1 image in the queue (newest)
        while not q.empty():
            q.get_nowait()

        q.put_nowait(img)
        q.join()


def detection_process(q, cv_q):
    global hotkey_to_shoot_pressed

    logging.info("DETECTION process started")
    det_classes = ['c', 'ch', 't', 'th']
    det_colors = [
        [115,185,245], #c
        [0,50,255], #ch
        [247,208,0], #t
        [247,82,0] #th
    ]
    detector = Detector(det_classes)
    detector.set_colors(det_colors)

    game_window_rect = get_game_windows_rect()
    # locker = Locker({
    #     "mouse_sen": 1, # min: 1, max: 2, default: 1
    #     "head_first": False,
    #     "mouse_smooth": 1.3, # min: 1, max: 3, default: 1.3
    #     "semi_delay": 0, # min: .1, max: 1, default: 0.1
    #     "recoil_sen": 0 # min: .5, max: 2, default: 1
    #     }, game_window_rect, head_list = [1, 3])

    # some preparations
    id_enemy_classes()
    keyboard.add_hotkey(CHANGE_TEAM_HOTKEY, change_team_hotkey_callback, args=('triggered', 'hotkey'))
    keyboard.add_hotkey(SHOOT_HOTKEY, shoot_hotkey_callback, args=('triggered', 'hotkey'))

    fov_mouse = FovMouseMovement(
        screen = game_window_rect,
        fov = (config["fov_mouse"]["fov_h"], config["fov_mouse"]["fov_v"]),
        x360 = config["fov_mouse"]["x360"],
        sensitivity = config["fov_mouse"]["sensitivity"])

    # loop
    while True:
        if not q.empty():
            try:
                img = q.get_nowait()
                bbox = None

                # Preprocess (predict, paint boxes, etc)
                # {'t': [{'cls': 2, 'conf': 0.9245539903640747, 'xyxy': [801.3914794921875, 179.41305541992188, 1124.4744873046875, 948.810791015625]}], 'th': [{'cls': 3, 'conf': 0.887331485748291, 'xyxy': [900.5308227539062, 178.01380920410156, 988.6021728515625, 313.15948486328125]}]}
                bbox = detector.detect(
                    img = img,
                    verbose = False,
                    half = False,
                    apply_nms = True,
                    nms_config = {"conf_thres": detect_threshold, "iou_thres": iou_threshold})

                # filter aim boxes (detect enemies only)
                filtered_bbox = detector.filter_rects(bbox, e_classes)

                if (hotkey_to_shoot_pressed or AUTO_SHOOT) and len(filtered_bbox):
                # if mouseWin32.is_left_mouse_down() and len(filtered_bbox):
                    # aims = convert_bbox_to_aims(filtered_bbox)
                    mouse_pos_x, mouse_pos_y = mouse.get_position()

                    # body_list = [x for x in aims if int(x[0]) not in heads_cls_list]
                    # head_list = [x for x in aims if int(x[0]) in heads_cls_list]

                    nearest_bbox, aim_coords, dist = get_nearest_bbox(filtered_bbox, game_window_rect)
                    print(f"Nearest is: {nearest_bbox}")

                    rel_move_angles = fov_mouse.get_move_angle(aim_coords)
                    print(f"Rel move angles is: {rel_move_angles}")

                    # rel_move_pixels = fov_mouse.get_rel_move_pixels(rel_move_angles)
                    # print(f"Rel move pixels is: {rel_move_pixels}")

                    mouseWin32.move_relative(int(rel_move_angles[0]), int(0))

                    if False:
                        # assist
                        mx = (aim_coords[0], mouse_pos_x)
                        my = (aim_coords[1], mouse_pos_y)
                        mouseWin32.move(aim_coords[0], aim_coords[1])
                        # mouseWin32.move_relative(
                        #     max(mx)+min(mx),
                        #     max(my)+min(my)
                        # )

                        if dist <= min_shoot_dist:
                            # shoot
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, mouse_pos_x, mouse_pos_y, 0, 0)
                            time.sleep(0.05)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, mouse_pos_x, mouse_pos_y, 0, 0)

                    hotkey_to_shoot_pressed = False


                # fbox = filtered_bbox[0]
                # print(f"Mouse current pos: {mouse.get_position()}")
                # print(f"Game rect is: {game_window_rect}")
                # print(f"Fbox found at: {fbox['xyxy'][0]}, {fbox['xyxy'][1]} (inside game rect)")
                # m_x = game_window_rect[0] + fbox['xyxy'][0]
                # m_y = game_window_rect[1] + fbox['xyxy'][1]
                # print(f"Moving mouse to: {m_x}, {m_y}")
                # mouse.move(m_x, m_y)

                # if len(aims):
                #     locker.lock(aims)
                # else:
                #     if recoil_mode:
                #         locker.recoil_only()
                #     locker.reset()

                q.task_done()
                if(config['cv2']['show_window']):
                    # CV paint detection boxes if required
                    if(config["cv2"]["paint_boxes"]):
                        # img = detector.paint_boxes(img, bbox, 0.5)
                        img = detector.paint_aim_boxes(img, filtered_bbox)

                    # display on CV side
                    while not cv_q.empty():
                        cv_q.get_nowait()

                    cv_q.put_nowait(img)
                    cv_q.join()
            except Empty:
                pass


def cv2_process(cv_q):
    global team

    if(not config['cv2']['show_window']):
        logging.info("CV2 process quit (show_windows is False)")

        sys.exit(1)
    else:
        logging.info("CV2 process started")

    fps = FPS()
    fps_font = cv2.FONT_HERSHEY_SIMPLEX

    # some preparations
    keyboard.add_hotkey(CHANGE_TEAM_HOTKEY, change_team_hotkey_callback, args=('triggered', 'hotkey'))

    while True:
        if not cv_q.empty():
            try:
                img = cv_q.get_nowait()
 
                # CV window stuff (fps, resize, etc)
                if config["cv2"]["show_window"]:
                    if config["cv2"]["show_fps"]:
                        img = cv2.putText(img, f"{fps():.2f}", (20, 120), fps_font,
                                          1.7, (0, 255, 0), 7, cv2.LINE_AA)

                    if config["cv2"]["resize_window"]:
                        img = cv2.resize(img, (config["cv2"]["window_width"], config["cv2"]["window_height"]))

                    if config["cv2"]["convert_rgb2bgr"]:
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                    if config["cv2"]["show_current_team"]:
                        if team.lower() == "ct":
                            img = cv2.putText(img, f"Team: CT", (20, 200), fps_font,
                                            1.2, (247,208,0), 7, cv2.LINE_AA)
                        else:
                            img = cv2.putText(img, f"Team: T", (20, 200), fps_font,
                                            1.2, (115,185,245), 7, cv2.LINE_AA)

                    cv2.imshow(config["cv2"]["title"], img)
                    cv2.waitKey(1)

                cv_q.task_done()
            except Empty:
                pass


if __name__ == "__main__":
    logging.info("Starting processes.")

    q = multiprocessing.JoinableQueue()
    cv_q = multiprocessing.JoinableQueue()
    p1 = multiprocessing.Process(target=grab_process, args=(q,), daemon = True)
    p2 = multiprocessing.Process(target=detection_process, args=(q,cv_q,), daemon = True)
    p3 = multiprocessing.Process(target=cv2_process, args=(cv_q,), daemon = True)

    p1.start()
    p2.start()
    p3.start()

    while True:
        if not p1.is_alive() or not p2.is_alive():
            sys.exit()
