from main import *
import time
from multiprocessing import Value
from uutils.torch_utils import time_synchronized

#####################################
#### Semi-Auto dataset collector ####
####      Provided "AS IS"       ####
####       AUTHOR: Priler        ####
####       ##############        ####
####          For YOLO           ####
#####################################


# CONFIG
# you can use either auto or manual capture mode
# suggested params for auto mode is:
# AUTO_GRAB_CAPTURE_DELAY = 0.5
# AUTO_GRAB_REQUIRED_CONF = 0.8
# but it's highly depends on your current model mAP & your needs
AUTO_GRAB = False # enable auto capture mode?
AUTO_GRAB_CAPTURE_DELAY = 1 # (auto-only) how much seconds to wait until next detected frame will be saved in dataset
AUTO_GRAB_REQUIRED_CONF = 0.7 # (auto-only) how much confidence required in order to save the detection

# (auto-only) if true, only full & equal detections will be saved to dataset
# i.e. ['t':1] will not be saved, but ['t':1, 'th':1] will be
# the same applies to equality, thefore ['t':1, 'th':2] will not be saved, but ['t':2, 'th':2] will be
# one more example: ['t':3, 'th':3, 'c': 2] will not be saved, but ['t':3, 'th':3, 'c': 2, 'ch': 2] will be saved
# in other words, full body & head detections will be now required.
# This should help avoid partial detections, as well as most of wrong ones.
AUTO_GRAB_REQUIRE_FULL_DETECTION = False

# grab hotkeys
MANUAL_GRAB_HOTKEY = 58  # 58 = CAPS-LOCK
AUTO_GRAB_TOGGLE_HOTKEY = 'f5'  # 58 = CAPS-LOCK

# dataset collecting paths etc.
DT_IMG_SAVE_PATH = "./data/collected/images/"
DT_LABEL_SAVE_PATH = "./data/collected/labels/"
# DT_LABEL_SAVE_PATH = DT_IMG_SAVE_PATH
DT_LABEL_FORMAT = "{id} {x_center_norm} {y_center_norm} {width_norm} {height_norm}"

# force detection team
DT_FORCE_TEAM = "auto" # auto, ct, t
DT_FORCE_CT_TEAM_HOTKEY = "f1"
DT_FORCE_T_TEAM_HOTKEY = "f2"
DT_FORCE_AUTO_TEAM_HOTKEY = "f3"

# VARS (do not touch)
manual_do_grab = False


def manual_grab_hotkey_callback(triggered, hotkey):
    global manual_do_grab
    manual_do_grab = True


def auto_grab_toggle_hotkey_callback(triggered, hotkey):
    global AUTO_GRAB
    AUTO_GRAB = not AUTO_GRAB


def force_auto_team_hotkey_callback(triggered, hotkey):
    global DT_FORCE_TEAM
    DT_FORCE_TEAM = "auto"
    print("Team force AUTO")


def force_ct_team_hotkey_callback(triggered, hotkey):
    global DT_FORCE_TEAM
    DT_FORCE_TEAM = "ct"
    print("Team force CT")


def force_t_team_hotkey_callback(triggered, hotkey):
    global DT_FORCE_TEAM
    DT_FORCE_TEAM = "t"
    print("Team force T")


def print_welcome_message():
    # some INFO
    print("\n\n\n[DATASET COLLECTOR by Priler (https://github.com/Priler)]")
    print("========================================")
    print(f"Press {str(MANUAL_GRAB_HOTKEY).upper()} in order to MANUAL GRAB current frame")
    print(f"Press {str(AUTO_GRAB_TOGGLE_HOTKEY).upper()} in order to toggle AUTO GRAB feature")
    print(f"Press {str(DT_FORCE_CT_TEAM_HOTKEY).upper()} in order to force CT team detection")
    print(f"Press {str(DT_FORCE_T_TEAM_HOTKEY).upper()} in order to force T team detection")
    print(f"Press {str(DT_FORCE_AUTO_TEAM_HOTKEY).upper()} in order to force AUTO team detection")
    print("~~~~~")
    print(f"Captured dataset images will be saved to: {DT_IMG_SAVE_PATH}")
    print(f"REQUIRE FULL DETECTION mode is " + "ON" if AUTO_GRAB_REQUIRE_FULL_DETECTION else "OFF")
    print(f"AUTO GRAB delay is set to {AUTO_GRAB_CAPTURE_DELAY} sec. with minimum of {AUTO_GRAB_REQUIRED_CONF} required confidence")
    print(".....")
    print("Starting ...\n\n\n")
    time.sleep(1)


def get_label_index(label):
    if label == "c":
        return 0
    elif label == "ch":
        return 1
    elif label == "t":
        return 2
    elif label == "th":
        return 3

def get_index_label(label):
    if label == 0:
        return "c"
    elif label == 1:
        return "ch"
    elif label == 2:
        return "t"
    elif label == "th":
        return 3


def dt_get_force_team_correction_table():
    global DT_FORCE_TEAM
    correction_table = ()

    if(DT_FORCE_TEAM == "t"):
        # force t team
        correction_table = (
            (0, 2), # c to t
            (1, 3), # ch to th
        )
        pass
    elif(DT_FORCE_TEAM == "ct"):
        # force ct team
        correction_table = (
            (2, 0), # t to c
            (3, 1), # th to ch
        )

    return correction_table


def gen_dt_label_content(label, xmin, ymin, xmax, ymax, image_width, image_height):
    global DT_LABEL_FORMAT, DT_FORCE_TEAM
    data = DT_LABEL_FORMAT

    label = int(label) # convert to int, in case it's a tensor

    x_center = (xmin + xmax) / 2
    y_center = (ymin + ymax) / 2

    x_center_norm = abs(x_center) / image_width
    y_center_norm = abs(y_center) / image_height 

    width_norm = abs(xmax-xmin) / image_width
    height_norm = abs(ymax-ymin) / image_height

    if(DT_FORCE_TEAM != "auto"):
        # force certain team
        correction_table = dt_get_force_team_correction_table()

        # apply force team patch
        for patch in correction_table:
            if label == patch[0]:
                label = patch[1]
                break

    # data = data.replace("{id}", str(get_label_index(label)))
    data = data.replace("{id}", str(label))
    data = data.replace("{x_center_norm}", "{:.4f}".format(x_center_norm))
    data = data.replace("{y_center_norm}", "{:.4f}".format(y_center_norm))
    data = data.replace("{width_norm}", "{:.4f}".format(width_norm))
    data = data.replace("{height_norm}", "{:.4f}".format(height_norm))

    return data


def save_dt_object(cv_img, label_content):
    global DT_IMG_SAVE_PATH, DT_LABEL_SAVE_PATH, monitor

    filename = "semi-auto-{game_title}_{ts}".format(game_title = config["grabber"]["window_title"], ts = time_synchronized())
    img_path = f"{DT_IMG_SAVE_PATH}{filename}.png"
    label_path = f"{DT_LABEL_SAVE_PATH}{filename}.txt"

    # save image file
    # mss.tools.to_png(mss_img.rgb, mss_img.size, output=img_path)
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(img_path, cv_img)

    # save label file
    with open(label_path, 'w') as f:
        f.write(label_content)

    return (img_path, label_path)


# custom detection process for 
def DT_detection_process(q, cv_q):
    logging.info("DT DETECTION process started")
    det_classes = ['c', 'ch', 't', 'th']
    det_colors = [
        [115,185,245], #c
        [0,50,255], #ch
        [247,208,0], #t
        [247,82,0] #th
    ]
    detector = Detector(det_classes)
    detector.set_colors(det_colors)

    global manual_do_grab, DT_FORCE_TEAM
    dt_last_capture = 0
    force_team_font = cv2.FONT_HERSHEY_SIMPLEX

    # manual grab hotkey
    keyboard.add_hotkey(MANUAL_GRAB_HOTKEY, manual_grab_hotkey_callback, args=('triggered', 'hotkey'))

    # auto grab toggle hotkey
    keyboard.add_hotkey(AUTO_GRAB_TOGGLE_HOTKEY, auto_grab_toggle_hotkey_callback, args=('triggered', 'hotkey'))

    # force team hotkeys
    keyboard.add_hotkey(DT_FORCE_AUTO_TEAM_HOTKEY, force_auto_team_hotkey_callback, args=('triggered', 'hotkey'))
    keyboard.add_hotkey(DT_FORCE_CT_TEAM_HOTKEY, force_ct_team_hotkey_callback, args=('triggered', 'hotkey'))
    keyboard.add_hotkey(DT_FORCE_T_TEAM_HOTKEY, force_t_team_hotkey_callback, args=('triggered', 'hotkey'))

    print_welcome_message()

    while True:
        if not q.empty():
            try:
                img = q.get_nowait()
                bbox = None

                # Preprocess (predict, paint boxes, etc)
                bbox = detector.detect(
                    img = img,
                    verbose = False,
                    half = False,
                    apply_nms = True,
                    nms_config = {"conf_thres": detect_threshold, "iou_thres": iou_threshold})

                # semi-auto dataset collecting
                do_grab = False

                _bkc = {}
                for k,v in bbox.items():
                    _bkc.setdefault(k, 0);
                    _bkc[k] += 1

                #if len(_bkc):
                if True:
                    # force bbox clrs, if required
                    if(DT_FORCE_TEAM != "auto"):
                        correction_table = dt_get_force_team_correction_table()
                        for cl in det_classes:
                            if cl in bbox:
                                for det in bbox[cl]:
                                    # apply force team patch
                                    for patch in correction_table:
                                        if det['cls'] == patch[0]:
                                            det['cls'] = patch[1]
                                            break

                    if not AUTO_GRAB:
                        # manual mode
                        if(manual_do_grab):
                            do_grab = True
                            manual_do_grab = False
                    else:
                        # auto mode
                        if (time_synchronized() - dt_last_capture) > AUTO_GRAB_CAPTURE_DELAY:
                            do_grab = True

                        if do_grab and AUTO_GRAB_REQUIRE_FULL_DETECTION:
                            # @TODO: sometimes passes [t: 2; th: 1]
                            _bkc_filtered = {}
                            for k,v in bbox.items():
                                _bkc_filtered.setdefault(k, 0)
                                if all(det['conf'] >= AUTO_GRAB_REQUIRED_CONF for det in v):
                                    _bkc_filtered[k] += 1
                            _bkc_fval = next(iter(_bkc_filtered.values()))
                            if(not all(v == _bkc_fval for v in _bkc_filtered.values())):
                                #print("EQUALITY ERROR")
                                do_grab = False

                            if not (len(_bkc_filtered) == 2 or len(_bkc_filtered) == 4):
                                #print("QUANTITY ERROR")
                                do_grab = False
                            elif len(_bkc_filtered) == 2:
                                if not ("c" in _bkc_filtered and "ch" in _bkc_filtered) and not ("t" in _bkc_filtered and "th" in _bkc_filtered):
                                    #print(f"CLASS ERROR {_bkc_filtered}")
                                    #print(("c" in _bkc_filtered and "ch" in _bkc_filtered))
                                    #print(("t" in _bkc_filtered and "th" in _bkc_filtered))
                                    do_grab = False

                        if do_grab:
                            dt_last_capture = time_synchronized()

                    if do_grab:
                        dataset_content = "" # FPs is allowed to be saved

                        for cl in det_classes:
                            if cl in bbox:
                                for det in bbox[cl]:
                                    if AUTO_GRAB and det['conf'] < AUTO_GRAB_REQUIRED_CONF:
                                        continue

                                    if dataset_content != "":
                                        dataset_content += "\n"

                                    # label, xmin, ymin, xmax, ymax, image_width, image_height
                                    dataset_content += gen_dt_label_content(det['cls'], det['xyxy'][0], det['xyxy'][1], det['xyxy'][2], det['xyxy'][3], img.shape[1], img.shape[0])

                        dt_save_result = save_dt_object(img, dataset_content)
                        print(f"+ Dataset item saved as {dt_save_result[0]}\n{_bkc}")

                q.task_done()
                if(config['cv2']['show_window']):
                    # CV paint detection boxes if required
                    if(config["cv2"]["paint_boxes"]):
                        img = detector.paint_boxes(img, bbox, 0.5)

                        if(DT_FORCE_TEAM == "auto"):
                            img = cv2.putText(img, f"Detection Team AUTO", (20, 200), force_team_font,
                                            1.5, (25, 25, 25), 7, cv2.LINE_AA)
                        elif(DT_FORCE_TEAM == "ct"):
                            img = cv2.putText(img, f"Detection Team CT", (20, 200), force_team_font,
                                            1.55, (115,185,245), 7, cv2.LINE_AA)
                        elif(DT_FORCE_TEAM == "t"):
                            img = cv2.putText(img, f"Detection Team T", (20, 200), force_team_font,
                                            1.7, (247,82,0), 7, cv2.LINE_AA)

                        if AUTO_GRAB:
                            img = cv2.putText(img, f"Auto Grab: TRUE", (20, 250), force_team_font,
                                            1, (153,199,148), 7, cv2.LINE_AA)
                        else:
                            img = cv2.putText(img, f"Auto Grab: FALSE", (20, 250), force_team_font,
                                            1, (48,56,65), 7, cv2.LINE_AA)

                    # display on CV side
                    while not cv_q.empty():
                        cv_q.get_nowait()

                    cv_q.put_nowait(img)
                    cv_q.join()
            except Empty:
                pass


if __name__ == "__main__":
    logging.info("Starting processes.")

    q = multiprocessing.JoinableQueue()
    cv_q = multiprocessing.JoinableQueue()
    p1 = multiprocessing.Process(target=grab_process, args=(q,), daemon = True)
    p2 = multiprocessing.Process(target=DT_detection_process, args=(q,cv_q,), daemon = True)
    p3 = multiprocessing.Process(target=cv2_process, args=(cv_q,), daemon = True)

    p1.start()
    p2.start()
    p3.start()

    while True:
        if not p1.is_alive() or not p2.is_alive():
            sys.exit()
