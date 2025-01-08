import cv2
from zones import ZONES
from helpers import draw_zones

from detector import Detector

if __name__ == "__main__":
    detector = Detector()
    cap = cv2.VideoCapture("data/beta1.mp4")

    while cap.isOpened():
        status, frame = cap.read()
        if not status:
            break

        frame = detector.process_frame(frame, ZONES)
        draw_zones(frame, ZONES, [(0, 0, 255), (0, 255, 0), (0, 0, 255), (255, 255, 255)])

        cv2.imshow("Detector", frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
