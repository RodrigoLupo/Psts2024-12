from datetime import datetime

class DateTimeIntervalCalculator:
    def __init__(self):
        self.last_datetime = None

    def get_current_datetime(self):
        """
        Obtiene el datetime actual.
        """
        return datetime.now()

    def calculate_interval(self, current_datetime):
        """
        Calcula el intervalo de tiempo en segundos (incluyendo milisegundos) 
        entre el último datetime registrado y el datetime actual.

        Args:
            current_datetime (datetime): El datetime actual.

        Returns:
            float: Intervalo en segundos (incluyendo milisegundos) o None si no hay referencia previa.
        """
        if self.last_datetime is None:
            self.last_datetime = current_datetime
            return None  # No hay intervalo si no hay un datetime previo

        interval = (current_datetime - self.last_datetime).total_seconds()
        self.last_datetime = current_datetime
        return interval

# Ejemplo de uso
if __name__ == "__main__":
    interval_calculator = DateTimeIntervalCalculator()

    # Simular detecciones de carros en un carril
    print("Carro detectado en carril verde.")
    current_time = interval_calculator.get_current_datetime()
    print(f"Datetime actual: {current_time}")

    interval = interval_calculator.calculate_interval(current_time)
    if interval is not None:
        print(f"Intervalo desde el último carro: {interval:.3f} segundos")
    else:
        print("Primer carro detectado, no hay intervalo previo.")

    # Simular otro carro después de un tiempo
    import time
    time.sleep(2.5)  # Esperar 2.5 segundos

    print("Carro detectado en carril verde.")
    current_time = interval_calculator.get_current_datetime()
    print(f"Datetime actual: {current_time}")

    interval = interval_calculator.calculate_interval(current_time)
    if interval is not None:
        print(f"Intervalo desde el último carro: {interval:.3f} segundos")
