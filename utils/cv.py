from typing import Tuple, List


def combine_bboxes(box1: Tuple[int, ...], box2: Tuple[int, ...]) -> Tuple[int, int, int, int]:
    box1_br = (box1[0] + box1[2], box1[1] + box1[3])
    box2_br = (box2[0] + box2[2], box2[1] + box2[3])

    x = min(box1[0], box2[0])
    y = min(box1[1], box2[1])
    w = max(box1_br[0], box2_br[0]) - x
    h = max(box1_br[1], box2_br[1]) - y

    return (x, y, w, h)


def xywh_to_xyxy(rect: Tuple[int, ...]) -> Tuple[int, int, int, int]:
    return (rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])


def xyxy_to_xywh(rect: Tuple[int, ...]) -> Tuple[int, int, int, int]:
    return (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])


def calc_iou(box_a: Tuple[int, ...], box_b: Tuple[int, ...]) -> float:
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    inter_area = max(0, x_b - x_a) * max(0, y_b - y_a)
    if inter_area == 0:
        return 0.0

    box_a_area = abs((box_a[2] - box_a[0]) * (box_a[3] - box_a[1]))
    box_b_area = abs((box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))

    return inter_area / float(box_a_area + box_b_area - inter_area)


def boxes_intersect(box1: Tuple[int, ...], box2: Tuple[int, ...]) -> bool:
    return calc_iou(xywh_to_xyxy(box1), xywh_to_xyxy(box2)) > 0


def merge_overlapping_boxes(boxes: List[Tuple[int, ...]]) -> List[Tuple[int, int, int, int]]:
    result = list(boxes)
    changed = True

    while changed:
        changed = False
        for i, box_i in enumerate(result):
            for j, box_j in enumerate(result):
                if i >= j:
                    continue
                if boxes_intersect(box_i, box_j):
                    merged = combine_bboxes(box_i, box_j)
                    result[i] = merged
                    result.pop(j)
                    changed = True
                    break
            if changed:
                break

    return result


def point_offset(src: Tuple[int, int], dst: Tuple[int, int]) -> Tuple[int, int]:
    return (dst[0] - src[0], dst[1] - src[1])


def round_to_multiple(value: int, multiple: int) -> int:
    return multiple * round(value / multiple)
