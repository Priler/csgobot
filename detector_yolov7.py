import sys
# sys.path[0] = "./yolov7"
# sys.path[1] = "./yolov7"
sys.path.append("./yolov7")

import numpy
import torch
import torch.backends.cudnn as cudnn
from numpy import random
import cv2
import time
import math

from yolov7.models.experimental import attempt_load
from yolov7.utils.datasets import LoadStreams, LoadImages
from yolov7.utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from yolov7.utils.plots import plot_one_box
from yolov7.utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

from configurator import config


class Detector:
    # yolov7 params
    weights = config["yolov7"]["weights"]  # model.pt path(s)
    img_size = int(config["yolov7"]["inference_size"])  # inference size (pixels)
    conf_thres = float(config["yolov7"]["conf_thres"])  # object confidence threshold (0.25 def)
    iou_thres = float(config["yolov7"]["iou_thres"])  # IOU threshold for NMS
    classes = None  # filter by class: --class 0, or --class 0 2 3
    agnostic_nms = False  # class-agnostic NMS
    augment = bool(config["yolov7"]["augment"])  # augmented inference
    device = config["yolov7"]["device"]  # cuda device, i.e. 0 or 0,1,2,3 or cpu
    source = 0  # file/folder, 0 for webcam
    trace = source
    no_trace = False  # don`t trace model

    _warmup_once = False

    def __init__(self, names):
        set_logging()

        # initialize
        self.device = select_device(self.device)
        self.half = self.device.type != 'cpu'

        # load model
        self.model = attempt_load(self.weights, map_location=self.device)  # load FP32 model
        self.stride = int(self.model.stride.max())  # model stride
        self.imgsz = check_img_size(self.img_size, s=self.stride)  # check img_size

        if self.trace:
            self.model = TracedModel(self.model, self.device, self.img_size)

        if self.half:
            self.model.half()  # to FP16

        # Second-stage classifier
        self.classify = False

        # cuDNN
        cudnn.benchmark = True  # set True to speed up constant image size inference

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else names
        self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

        # Run inference
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once

    def set_colors(self, new_colors):
        self.colors = new_colors

    def get_cls_label(self, _cls):
        return self.names[_cls]

    def detect(self, img: numpy.ndarray) -> dict:
        """
        Make an inference (prediction) of a given image.
        Image size must be multiple of 32 (ex. 640).
        And the channels count must be 3 (RGB).
        :param img: Input image, must be numpy.ndarray with shape of (samples, channels, height, width).
        :return: Detected bounding boxes in a dict format, where's the key is a class.
        """

        # get some img data
        img_height, img_width, img_channels = img.shape

        img0 = img  # preserve for plotting & displaying
        if img_channels > 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # leave 3 channels

        # reshape for PyTorch (samples, channels, height, width)
        img = numpy.moveaxis(img, -1, 0)

        old_img_w = old_img_h = self.imgsz
        old_img_b = 1
        t0 = time.time()

        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # print(img.size())
        # pad image dimensions to be multiple of 32 (ex. 1280x720 to 1312x736)
        # note.
        # Keras format is (samples, height, width, channels)
        # PyTorch is (samples, channels, height, width)
        if config['yolov7']['resize_image_to_fit_multiply_of_32']:
            padding1_mult = math.floor(img.shape[2] / 32) + 1
            padding2_mult = math.floor(img.shape[3] / 32) + 1
            pad1 = (32 * padding1_mult) - img.shape[2]
            pad2 = (32 * padding2_mult) - img.shape[3]
            padding = torch.nn.ReplicationPad2d((0, pad2, pad1, 0, 0, 0))

            img = padding(img)

        if self._warmup_once:
            # Warmup
            if self.device.type != 'cpu' and (
                    old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
                old_img_b = img.shape[0]
                old_img_h = img.shape[2]
                old_img_w = img.shape[3]
                for i in range(3):
                    self.model(img, augment=self.augment)[0]

            self._warmup_once = False

        # Inference
        t1 = time_synchronized()
        with torch.no_grad():  # Calculating gradients would cause a GPU memory leak
            pred = self.model(img, augment=self.augment)[0]
        t2 = time_synchronized()

        # Apply NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=self.classes, agnostic=self.agnostic_nms)
        t3 = time_synchronized()

        # Process detections
        result = {}
        for i, det in enumerate(pred):  # detections per image
            s = ''

            gn = torch.tensor(img0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                # Rescale boxes from img_size to img0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {self.names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Gather results
                for *xyxy, conf, cls in reversed(det):
                    result.setdefault(self.names[int(cls)], [])

                    result[self.names[int(cls)]].append({
                        "cls": cls,
                        "conf": conf,
                        "xyxy": xyxy
                    })

        return result


    def filter_rects(self, bbox_list: dict, e_classes: list):
        filtered_rects = []

        for i, (c, ds) in enumerate(bbox_list.items()):
            if c in e_classes:
                for d in ds:
                    aim_box = {
                        "tcls": c,
                        "cls": d["cls"],
                        "conf": d["conf"],
                        "xyxy": d["xyxy"]
                    }
                    filtered_rects.append(aim_box)

        return filtered_rects


    def paint_boxes(self, img: numpy.ndarray, bbox_list: dict, min_conf: float) -> numpy.ndarray:
        """
        Paint predicted bounding boxes to a given image.
        :param img: Input image.
        :param bbox_list: Detected bounding boxes (expected output from detect method).
        :return:
        """
        for i, (c, ds) in enumerate(bbox_list.items()):
            for d in ds:
                if float(d['conf']) > min_conf:
                    plot_one_box(d["xyxy"], img, label=f"{self.get_cls_label(int(d['cls']))} {d['conf']:.2f}", color=self.colors[int(d["cls"])], line_thickness=2)

        return img


    def paint_aim_boxes(self, img: numpy.ndarray, aims_list: list) -> numpy.ndarray:
        """
        Paint aims bounding boxes to a given image.
        :param img: Input image.
        :param aims_list: Detected aim boxes (expected output from filter_rects method).
        :return:
        """
        for aim in aims_list:
            self.plot_one_box(aim["xyxy"], img, label=f"{aim['tcls']} {aim['conf']:.2f}", color=self.colors[int(aim["cls"])], line_thickness=2)

        return img
