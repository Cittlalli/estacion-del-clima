import machine
import uos as os
import sdcard
import time

class SDLogger:
    """
    Clase para registrar y gestionar datos en una tarjeta SD.

    Atributos:
        spi+: Objeto SPI para comunicación con la SD.
        cs: Pin chip select.
        mount_point+: Punto de montaje de la SD.
        sd}: Objeto SDCard.
        filepath (str): Ruta del archivo actual de registro.
        current_date (int): Día actual (usado para rotar el archivo diario).
        sd_montada (bool): Estado de montaje de la SD.
    """

    def __init__(self, spi_id, sck_pin, mosi_pin, miso_pin, cs_pin):
        """
        Inicializa el SPI y prepara los pines para la tarjeta SD.

        Args:
            spi_id (int): ID del bus SPI.
            sck_pin (int): Pin del reloj SPI.
            mosi_pin (int): Pin MOSI.
            miso_pin (int): Pin MISO.
            cs_pin (int): Pin chip select.
        """
        self.spi = machine.SPI(
            spi_id,
            baudrate=1000000,
            polarity=0,
            phase=0,
            sck=machine.Pin(sck_pin),
            mosi=machine.Pin(mosi_pin),
            miso=machine.Pin(miso_pin),
        )
        self.cs = machine.Pin(cs_pin, machine.Pin.OUT)
        self.mount_point = '/sd'
        self.sd = None
        self.filepath = None
        self.current_date = None
        self.sd_montada = False

    def init_sd(self):
        """
        Intenta montar la tarjeta SD. Si ya está montada, primero la desmonta.

        Raises:
            Exception: Si ocurre un error al montar la SD.
        """
        try:
            try:
                os.umount(self.mount_point)
            except:
                pass
            self.sd = sdcard.SDCard(self.spi, self.cs)
            os.mount(self.sd, self.mount_point)
            self.sd_montada = True
            print("[OK] SD Card montada en", self.mount_point)
        except Exception as e:
            self.sd_montada = False
            print("❌ Error montando SD:", e)
            raise

    def get_today_filename(self):
        """
        Genera el nombre del archivo CSV basado en la fecha actual.

        Returns:
            str: Ruta completa del archivo del día actual.
        """
        t = time.localtime()
        return "{}/lecturas_{:04d}-{:02d}-{:02d}.csv".format(
            self.mount_point, t[0], t[1], t[2]
        )

    def check_daily_file(self):
        """
        Verifica si el archivo de hoy existe. Si no, lo crea con encabezados.
        Solo opera si la SD está montada.
        """
        if not self.sd_montada:
            return
        t = time.localtime()
        today = t[2]
        if today != self.current_date:
            self.current_date = today
            self.filepath = self.get_today_filename()
            try:
                with open(self.filepath, "x") as f:
                    f.write("Hora,Temperatura,Presion,Humedad\n")
                print(f"[OK] Archivo creado: {self.filepath}")
            except OSError:
                print(f"[INFO] Archivo ya existe: {self.filepath}")

    def log_data(self, temperatura, presion, humedad):
        """
        Registra una línea de datos en el archivo CSV del día.

        Args:
            temperatura (float): Temperatura en °C.
            presion (float): Presión en hPa.
            humedad (float): Humedad relativa en %.
        """
        if not self.sd_montada:
            print("⚠️ SD no disponible, no se puede guardar.")
            return
        self.check_daily_file()
        self.limpiar_si_espacio_bajo(minimo_porcentaje_libre=0.10)
        try:
            hora = "{:02d}:{:02d}:{:02d}".format(*time.localtime()[3:6])
            with open(self.filepath, 'a') as f:
                linea = f"{hora},{temperatura},{presion},{humedad}\n"
                f.write(linea)
                print(f"[SD] Datos registrados: {linea.strip()}")
        except Exception as e:
            print("❌ Error escribiendo en SD:", e)
            self.sd_montada = False

    def leer_ultimo_dato(self):
        """
        Lee la última línea de datos registrada en el archivo actual.

        Returns:
            str or None: Última línea de datos, o `None` si no hay datos disponibles.
        """
        if not self.sd_montada:
            self.intentar_reconexion()
        if not self.sd_montada:
            return None
        self.check_daily_file()
        try:
            with open(self.filepath, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    return lines[-1].strip()
        except Exception as e:
            print("Error leyendo último dato:", e)
            self.sd_montada = False
        return None

    def intentar_reconexion(self):
        """
        Intenta montar nuevamente la SD si no está montada.
        """
        if not self.sd_montada:
            print("🔄 Intentando reconectar SD...")
            self.init_sd()

    def limpiar_si_espacio_bajo(self, minimo_porcentaje_libre=0.10):
        """
        Elimina archivos antiguos si el espacio libre en la SD es menor al umbral dado.

        Args:
            minimo_porcentaje_libre (float): Porcentaje mínimo requerido de espacio libre.
        """
        try:
            stats = os.statvfs(self.mount_point)
            espacio_total = stats[0] * stats[2]
            espacio_libre = stats[0] * stats[3]
            porcentaje_libre = espacio_libre / espacio_total
            print(f"Bloque: {stats[0]}, Total bloques: {stats[2]}, Libres: {stats[3]}")
            print(f"Espacio total: {espacio_total / 1024:.2f} KB")
            print(f"Espacio libre: {espacio_libre / 1024:.2f} KB")
            print(f"[SD] Espacio libre: {porcentaje_libre:.2%}")

            while porcentaje_libre < minimo_porcentaje_libre:
                archivos = [
                    f for f in os.listdir(self.mount_point)
                    if f.startswith("lecturas_") and f.endswith(".csv")
                ]
                if not archivos:
                    print("ℹ️ No hay archivos para borrar.")
                    return

                archivos.sort()  # más antiguo al principio
                archivo_mas_antiguo = archivos[0]
                try:
                    os.remove(f"{self.mount_point}/{archivo_mas_antiguo}")
                    print(f"🗑 Archivo eliminado: {archivo_mas_antiguo}")
                except Exception as e:
                    print(f"❌ Error al eliminar {archivo_mas_antiguo}:", e)
                    break

                # Recalcular espacio
                stats = os.statvfs(self.mount_point)
                espacio_total = stats[0] * stats[2]
                espacio_libre = stats[0] * stats[3]
                porcentaje_libre = espacio_libre / espacio_total
        except Exception as e:
            print("❌ Error al comprobar espacio en SD:", e)
