import warnings
import torch
from tracker import Sort
from helpers import draw_detections, is_inside_zone
from calculador_datetime import DateTimeIntervalCalculator
from ventana import Logger
from database import DatabaseHandler

warnings.filterwarnings("ignore", category=FutureWarning)

class Detector:
    def __init__(self, model_name="yolov5n", confidence_threshold=0.15):
        """
        Inicializa el detector de vehículos con YOLOv5 y otros componentes necesarios.
        """
        # Cargar modelo de detección YOLOv5
        self.model = torch.hub.load("ultralytics/yolov5", model=model_name, pretrained=True)
        self.confidence_threshold = confidence_threshold

        # Inicializar tracker para autos
        self.tracker = Sort()

        # Estados de vehículos por zonas
        self.vehicle_states = {
            'green': {},  # Estructura: {id: {'state': 'inside'/'exited'/'completed', 'enter_time': datetime, 'detection_id': int}}
            'red': {},
        }

        # Contador global de detecciones
        self.global_counter = 0  # Contador único para todos los vehículos
        self.lane_counters = {
            'green': 0,
            'red': 0,
        }
        # Inicializar calculador de intervalos de tiempo
        self.interval_calculator = DateTimeIntervalCalculator()

        # Inicializar logger para manejar registros
        self.logger = Logger()

        # Inicializar manejador de base de datos
        self.db_handler = DatabaseHandler()

    def get_bboxes(self, preds, name_filter):
        """
        Obtiene los bounding boxes de las predicciones filtrando por nombre y confianza.
        """
        df = preds.pandas().xyxy[0]
        return df[(df["confidence"] >= self.confidence_threshold) & (df["name"] == name_filter)][['xmin', 'ymin', 'xmax', 'ymax']].values

    def update_vehicle_state(self, vehicle_id, zone, is_inside, current_time):
        """
        Actualiza el estado de un vehículo en una zona específica.
        """
        vehicle = self.vehicle_states[zone].get(vehicle_id, None)

        if is_inside:  # Vehículo entrando o dentro de la zona
            if not vehicle or vehicle['state'] == 'completed':  # Nueva detección
                # Incrementar el contador global para asignar un nuevo ID único
                self.global_counter += 1
                detection_id = self.global_counter

                # Calcular intervalo con el vehículo previo
                interval = self.interval_calculator.calculate_interval(current_time, zone)
                self.lane_counters[zone] += 1

                # Registrar entrada del vehículo
                self.vehicle_states[zone][vehicle_id] = {
                    'state': 'inside',
                    'enter_time': current_time,
                    'detection_id': detection_id,
                }

                # Guardar en la base de datos y el logger
                self.db_handler.save_detection(zone, current_time, interval, self.lane_counters[zone])
                self.logger.add_entry_log(zone, detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"), interval, self.lane_counters[zone])
        else:  # Vehículo saliendo de la zona
            if vehicle and vehicle['state'] == 'inside':  # Cambio a estado "exited"
                vehicle['state'] = 'exited'
                vehicle['exit_time'] = current_time

                # Usar el detection_id registrado al entrar
                detection_id = vehicle['detection_id']

                # Actualizar salida en la base de datos y logger
                self.db_handler.update_exit_time(detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"))
                self.logger.add_exit_log(zone, detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"))

                # Marcar como completado
                vehicle['state'] = 'completed'

    def process_frame(self, frame, zones):
        """
        Procesa cada frame, detectando vehículos, actualizando sus estados y registrando entradas/salidas.
        """
        preds = self.model(frame)
        frame_data = self.tracker.update(self.get_bboxes(preds, "car"))
        current_time = self.interval_calculator.get_current_datetime()

        for obj in frame_data:
            xc, yc = draw_detections(frame, obj, (255, 0, 0), (0, 255, 0))

            # Manejo de zona verde
            is_inside_green = is_inside_zone((xc, yc), zones['car_green'])
            self.update_vehicle_state(obj[4], 'green', is_inside_green, current_time)

            # Manejo de zona roja
            is_inside_red = is_inside_zone((xc, yc), zones['car_red'])
            self.update_vehicle_state(obj[4], 'red', is_inside_red, current_time)

        # Mostrar logs en la ventana
        self.logger.display_logs(frame)
        self.logger.display_exit_logs(frame)
        return frame
