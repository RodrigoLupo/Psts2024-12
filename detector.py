import warnings
import torch
from tracker import Sort
from helpers import draw_detections, is_inside_zone
from calculador_datetime import DateTimeIntervalCalculator
from ventana import Logger
from database import DatabaseHandler

warnings.filterwarnings("ignore", category=FutureWarning)

class Detector:
    def __init__(self, model_name="yolov5n", confidence_threshold=0.30):
        """
        Inicializa el detector de vehículos con YOLOv5 y otros componentes necesarios.
        """
        # Cargar modelo de detección YOLOv5
        self.model = torch.hub.load("ultralytics/yolov5", model=model_name, pretrained=True)
        self.confidence_threshold = confidence_threshold

        # Inicializar trackers para autos y buses
        self.trackers = {
            'car': Sort(),
            'bus': Sort(),
        }

        # Estados de vehículos por zonas
        self.vehicle_states = {
            'green': {},  # Estructura: {id: {'state': 'inside'/'exited'/'completed', 'enter_time': datetime}}
            'red': {},
        }

        # Contadores de detecciones por zonas
        self.counters = {
            'green': 0,  # Total acumulado en la zona verde
            'red': 0,    # Total acumulado en la zona roja
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
                self.counters[zone] += 1
                
                # Calcular intervalo con el vehículo previo
                interval = self.interval_calculator.calculate_interval(current_time, zone)
                
                # Registrar entrada del vehículo
                self.vehicle_states[zone][vehicle_id] = {
                    'state': 'inside',
                    'enter_time': current_time,
                }
                
                # Guardar en la base de datos y el logger
                detection_id = self.db_handler.save_detection(zone, current_time, interval, self.counters[zone])
                self.logger.add_entry_log(zone, detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"), interval, self.counters[zone])
        else:  # Vehículo saliendo de la zona
            if vehicle and vehicle['state'] == 'inside':  # Cambio a estado "exited"
                vehicle['state'] = 'exited'
                vehicle['exit_time'] = current_time
                
                # Actualizar salida en la base de datos y logger
                detection_id = self.counters[zone]  # Usamos el mismo contador para entrada y salida
                self.db_handler.update_exit_time(detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"))
                self.logger.add_exit_log(zone, detection_id, current_time.strftime("%Y-%m-%d %H:%M:%S"))
                
                # Marcar como completado
                vehicle['state'] = 'completed'

    def process_frame(self, frame, zones):
        """
        Procesa cada frame, detectando vehículos, actualizando sus estados y registrando entradas/salidas.
        """
        preds = self.model(frame)
        frame_data = {
            'cars': self.trackers['car'].update(self.get_bboxes(preds, "car")),
            'buses': self.trackers['bus'].update(self.get_bboxes(preds, "bus")),
        }
        current_time = self.interval_calculator.get_current_datetime()

        for vehicle_type, data in [('car', frame_data['cars']), ('bus', frame_data['buses'])]:
            for obj in data:
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
