import warnings
import torch
import numpy as np
from tracker import Sort
from helpers import resize_frame, draw_zones, draw_detections, is_inside_zone
from calculador_datetime import DateTimeIntervalCalculator
from ventana import Logger
from database import DatabaseHandler

warnings.filterwarnings("ignore", category=FutureWarning)


class Detector:
    def __init__(self, model_name="yolov5n", confidence_threshold=0.30):
        self.model = torch.hub.load("ultralytics/yolov5", model=model_name, pretrained=True)
        self.confidence_threshold = confidence_threshold
        self.trackers = {
            'car': Sort(),
            'bus': Sort(),
            'person': Sort()
        }
        self.countend_ids = {
            'person': set(),
            'green': set(),
            'red': set(),
            'exit': set()
        }
        self.car_ids = {
            'green': 0,
            'red': 0,
            'exit': 0
        }
        self.counters = {
            'person': 0,
            'green': 0,
            'red': 0,
            'exit': 0
        }
        self.interval_calculator = DateTimeIntervalCalculator()
        self.logger = Logger()
        self.db_handler = DatabaseHandler()

        self.person_counter = 1

    def get_bboxes(self, preds, name_filter):
        df = preds.pandas().xyxy[0]
        return df[(df["confidence"] >= self.confidence_threshold) & (df["name"] == name_filter)][['xmin', 'ymin', 'xmax', 'ymax']].values

    def process_frame(self, frame, zones):
        preds = self.model(frame)
        frame_data = {
            'cars': self.trackers['car'].update(self.get_bboxes(preds, "car")),
            'buses': self.trackers['bus'].update(self.get_bboxes(preds, "bus")),
            'people': self.trackers['person'].update(self.get_bboxes(preds, "person"))
        }

        # Asegurar consistencia en las formas de datos
        cars = frame_data['cars'] if frame_data['cars'].size > 0 else np.empty((0, 5))
        buses = frame_data['buses'] if frame_data['buses'].size > 0 else np.empty((0, 5))

        # Combinar datos de carros y buses
        combined_vehicles = np.concatenate((cars, buses), axis=0) if cars.size > 0 or buses.size > 0 else np.empty((0, 5))

        for obj in combined_vehicles:
            xc, yc = draw_detections(frame, obj, (255, 0, 0), (0, 255, 0))
            current_time = self.interval_calculator.get_current_datetime()

            if is_inside_zone((xc, yc), zones['car_green']) and obj[4] not in self.countend_ids['green']:
                self.countend_ids['green'].add(obj[4])
                self.counters['green'] += 1
                self.car_ids['green'] += 1
                interval = self.interval_calculator.calculate_interval(current_time)
                self.logger.add_log('green', self.car_ids['green'], current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    interval if interval else 0.0, self.counters['green'])

                # Guardar en la base de datos
                self.db_handler.save_detection("green", current_time, interval if interval else 0.0, self.counters['green'])

            elif is_inside_zone((xc, yc), zones['car_red']) and obj[4] not in self.countend_ids['red']:
                self.countend_ids['red'].add(obj[4])
                self.counters['red'] += 1
                self.car_ids['red'] += 1
                interval = self.interval_calculator.calculate_interval(current_time)
                self.logger.add_log('red', self.car_ids['red'], current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    interval if interval else 0.0, self.counters['red'])

                # Guardar en la base de datos
                self.db_handler.save_detection("red", current_time, interval if interval else 0.0, self.counters['red'])

            elif is_inside_zone((xc, yc), zones['exit']) and obj[4] not in self.countend_ids['exit']:
                self.countend_ids['exit'].add(obj[4])
                self.counters['exit'] += 1
                self.car_ids['exit'] += 1
                interval = self.interval_calculator.calculate_interval(current_time)
                self.logger.add_log('exit', self.car_ids['exit'], current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    interval if interval else 0.0, self.counters['exit'])

                # Guardar en la base de datos
                self.db_handler.save_detection("exit", current_time, interval if interval else 0.0, self.counters['exit'])

        for obj in frame_data['people']:
            xc, yc = draw_detections(frame, obj, (0, 255, 255), (255, 255, 255), is_person=True)
            if is_inside_zone((xc, yc), zones['person']) and obj[4] not in self.countend_ids['person']:
                self.countend_ids['person'].add(obj[4])
                self.counters['person'] += 1

                person_id = self.person_counter
                self.person_counter += 1

                print(f"Persona detectada en zona peatonal. ID: {person_id}, Posición: ({xc}, {yc})")

        self.logger.display_logs(frame)
        return frame