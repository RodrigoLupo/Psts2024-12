from collections import deque
import cv2

class Logger:
    def __init__(self):
        self.logs = {
            'green': deque(maxlen=3),
            'red': deque(maxlen=3),
        }
        self.exit_logs = {
            'green': deque(maxlen=3),
            'red': deque(maxlen=3),
        }
        self.counters = {
            'green': 0,  # Contador total de carros en el carril verde
            'red': 0     # Contador total de carros en el carril rojo
        }

    def add_entry_log(self, carril, car_id, timestamp, interval, total_count):
        """Agrega un registro de entrada al carril correspondiente."""
        self.logs[carril].append((car_id, timestamp, interval))
        self.counters[carril] = total_count

    def add_exit_log(self, carril, car_id, exit_time):
        """Agrega un registro de salida al carril correspondiente."""
        self.exit_logs[carril].append((car_id, exit_time))

    def display_logs(self, frame):
        """Muestra los últimos registros de entrada en el video."""
        for carril, color, y_offset in [('green', (0, 255, 0), 30), ('red', (0, 0, 255), 150)]:
            # Mostrar el contador total del carril
            cv2.putText(frame, f"Carril {carril.upper()}: Total: {self.counters[carril]}",
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
            cv2.putText(frame, f"Carril {carril.upper()}: Total: {self.counters[carril]}",
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Mostrar los últimos registros del carril
            for i, (log_id, log_time, log_interval) in enumerate(self.logs[carril]):
                text = f"ID: {log_id}, Fecha: {log_time}, Intervalo: {log_interval:.2f}s"
                y_pos = y_offset + 25 * (i + 1)

                # Texto con borde negro
                cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def display_exit_logs(self, frame):
        """Muestra los últimos registros de salida en el video."""
        for carril, y_offset in [('green', 60), ('red', 180)]:
            for i, (car_id, exit_time) in enumerate(self.exit_logs[carril]):
                text = f"Salida - ID: {car_id}, Hora: {exit_time}"
                y_pos = y_offset + 25 * (i + 1)

                # Mostrar salida en rojo
                cv2.putText(frame, text, (400, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                cv2.putText(frame, text, (400, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
