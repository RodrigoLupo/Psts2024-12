import mysql.connector


class DatabaseHandler:
    def __init__(self, host="localhost", user="root", password="1234", database="detector_db"):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()

        # Crear tabla si no existe
        self._create_table()

    def _create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS detections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zone VARCHAR(10),
            entry_time DATETIME,
            interval_time FLOAT,
            count INT
        );
        """
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def save_detection(self, zone, entry_time, interval_time, count):
        insert_query = """
        INSERT INTO detections (zone, entry_time, interval_time, count)
        VALUES (%s, %s, %s, %s);
        """
        self.cursor.execute(insert_query, (zone, entry_time, interval_time, count))
        self.connection.commit()

    def close_connection(self):
        self.cursor.close()
        self.connection.close()
