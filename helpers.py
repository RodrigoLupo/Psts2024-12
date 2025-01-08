import cv2
import matplotlib.path as mplPath


def resize_frame(frame, width=1024):
    h, w = frame.shape[:2]
    return cv2.resize(frame, (width, int(h * (width / w))))

def draw_zones(frame, zones, colors):
    for zone, color in zip(zones.values(), colors):
        cv2.polylines(frame, [zone], isClosed=True, color=color, thickness=2)

def draw_detections(frame, obj, color, point_color, is_person=False):
    x1, y1, x2, y2, tid = obj
    xc, yc = (int((x1 + x2) / 2), int((y1 + y2) / 2)) if is_person else (int((x1 + x2) / 2), int(y2))
    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
    cv2.circle(frame, (xc, yc), 5, point_color, -1)
    return xc, yc

def is_inside_zone(point, zone):
    return mplPath.Path(zone).contains_point(point)
