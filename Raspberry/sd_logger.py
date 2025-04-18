import machine
import uos
import sdcard
import time

class SDLogger:
    def __init__(self, spi_id, sck_pin, mosi_pin, miso_pin, cs_pin):
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
        try:
            try:
                uos.umount(self.mount_point)
            except:
                pass

            self.sd = sdcard.SDCard(self.spi, self.cs)
            uos.mount(self.sd, self.mount_point)
            self.sd_montada = True
            print("[OK] SD Card montada en", self.mount_point)
        except Exception as e:
            self.sd_montada = False
            print("❌ Error montando SD:", e)
            raise

    def get_today_filename(self):
        t = time.localtime()
        return "{}/lecturas_{:04d}-{:02d}-{:02d}.csv".format(
            self.mount_point, t[0], t[1], t[2]
        )

    def check_daily_file(self):
        if not self.sd_montada:
            return
        today = time.localtime()[:3]
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
        Registra una línea con datos de sensores en el archivo CSV del día.

        :param temperatura: Valor de temperatura.
        :param presion: Valor de presión.
        :param humedad: Valor de humedad.
        """
        
        if not self.sd_montada:
            print("⚠️ SD no disponible, no se puede guardar.")
            return
        self.check_daily_file()
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
        if not self.sd_montada:
            print("🔄 Intentando reconectar SD...")
            self.init_sd()
