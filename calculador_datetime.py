from datetime import datetime

class DateTimeIntervalCalculator:
    def __init__(self):
        # Diccionario para almacenar el último tiempo de entrada por zona
        self.last_entry_time = {}

    def get_current_datetime(self):
        """
        Obtiene el datetime actual.
        """
        return datetime.now()

    def calculate_interval(self, current_time, zone):
        """
        Calcula el intervalo de tiempo en segundos entre la entrada del último vehículo y el actual en una zona específica.
        """
        # Obtener el último tiempo de entrada para la zona
        last_time = self.last_entry_time.get(zone, None)

        # Actualizar el tiempo de entrada actual en el diccionario
        self.last_entry_time[zone] = current_time

        if not last_time:
            # Si no hay un registro previo, devuelve 0 como intervalo
            return 0.0

        # Calcular el intervalo de tiempo en segundos
        interval = (current_time - last_time).total_seconds()
        return interval