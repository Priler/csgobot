import cv2
import numpy

def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6: # if there are more than 5 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports,non_working_ports


def combine_bounding_box(box1, box2):
    box1_size = (box1[0] + box1[2], box1[1] + box1[3])
    box2_size = (box2[0] + box2[2], box2[1] + box2[3])

    x = min(box1[0], box2[0])
    y = min(box1[1], box2[1])
    w = max(box1_size[0], box2_size[0])
    h = max(box1_size[1], box2_size[1])
    return x, y, w - x, h - y


def convert_rectangle_to_xyxy(rect):
    return rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]


def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    # interArea = abs(max((xB - xA, 0)) * max((yB - yA), 0))
    interArea = max((xB - xA), 0) * max((yB - yA), 0)
    if interArea == 0:
        return 0
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = abs((boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = abs((boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou


def check_intersection(box1, box2):
    # crutch, but works :3
    return not bb_intersection_over_union(convert_rectangle_to_xyxy(box1), convert_rectangle_to_xyxy(box2)) == 0


def filter_rectangles(rect_list: list) -> list:
    """
    Filter given rect_list with selected filter type and return.
    :param rect_list: Rectangles list.
    :param filter_type: 1 to filter INSIDE, -1 to filter OUTSIDE, 0 to filter INTERSECTED
    :return:
    """

    changes = True
    while changes:
        changes = False

        for k, v in enumerate(rect_list):
            for rk, r in enumerate(rect_list):
                if rk == k:
                    continue

                # print(f"v: {v}, r: {r}, I - {check_intersection(v, r)}")
                if check_intersection(v, r):
                    v = combine_bounding_box(v, r)
                    rect_list.pop(rk)
                    rect_list[k] = v
                    changes = True
                    break

            if changes:
                break

    return rect_list


def point_get_difference(source_point, dest_point):
    # 1000, 1000
    # source_point = (960, 540)
    # dest_point = (833, 645)
    # result = (100, 100)

    x = dest_point[0]-source_point[0]
    y = dest_point[1]-source_point[1]

    return x, y


def round_to_multiple(number, multiple):
    return multiple * round(number / multiple)
