import time
from machine import I2C

# Definiciones de registros del BMP280
REG_CONFIG = 0xF5
REG_CTRL_MEAS = 0xF4
REG_PRESSURE_MSB = 0xF7
REG_TEMP_MSB = 0xFA
REG_DIG_START = 0x88
NUM_CALIB_PARAMS = 24

class BMP280:
    def __init__(self, i2c, address=0x76):
        # Se requiere que se le pase el objeto I2C ya configurado (por ejemplo, con SDA y SCL definidos en main)
        self.i2c = i2c
        self.address = address
        self.calib_params = {}
        self._load_calibration()
        self._initialize_sensor()

    def _load_calibration(self):
        data = self.i2c.readfrom_mem(self.address, REG_DIG_START, NUM_CALIB_PARAMS)
        data = list(data)
        self.calib_params = {
            "dig_t1": data[1] << 8 | data[0],
            "dig_t2": (data[3] << 8 | data[2]) - 0x10000 if data[3] & 0x80 else data[3] << 8 | data[2],
            "dig_t3": (data[5] << 8 | data[4]) - 0x10000 if data[5] & 0x80 else data[5] << 8 | data[4],
            "dig_p1": data[7] << 8 | data[6],
            "dig_p2": (data[9] << 8 | data[8]) - 0x10000 if data[9] & 0x80 else data[9] << 8 | data[8],
            "dig_p3": (data[11] << 8 | data[10]) - 0x10000 if data[11] & 0x80 else data[11] << 8 | data[10],
            "dig_p4": (data[13] << 8 | data[12]) - 0x10000 if data[13] & 0x80 else data[13] << 8 | data[12],
            "dig_p5": (data[15] << 8 | data[14]) - 0x10000 if data[15] & 0x80 else data[15] << 8 | data[14],
            "dig_p6": (data[17] << 8 | data[16]) - 0x10000 if data[17] & 0x80 else data[17] << 8 | data[16],
            "dig_p7": (data[19] << 8 | data[18]) - 0x10000 if data[19] & 0x80 else data[19] << 8 | data[18],
            "dig_p8": (data[21] << 8 | data[20]) - 0x10000 if data[21] & 0x80 else data[21] << 8 | data[20],
            "dig_p9": (data[23] << 8 | data[22]) - 0x10000 if data[23] & 0x80 else data[23] << 8 | data[22]
        }
    
    def _initialize_sensor(self):
        # Escribir configuración en el sensor
        self.i2c.writeto_mem(self.address, REG_CONFIG, bytes([(0x04 << 5) | (0x05 << 2)]))
        self.i2c.writeto_mem(self.address, REG_CTRL_MEAS, bytes([(0x01 << 5) | (0x03 << 2) | 0x03]))
        time.sleep(0.1)
    
    def read_raw_data(self):
        data = self.i2c.readfrom_mem(self.address, REG_PRESSURE_MSB, 6)
        data = list(data)
        raw_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return raw_temp, raw_pressure

    def convert_temp(self, raw_temp):
        params = self.calib_params
        var1 = (((raw_temp >> 3) - (params["dig_t1"] << 1)) * params["dig_t2"]) >> 11
        var2 = (((((raw_temp >> 4) - params["dig_t1"]) * ((raw_temp >> 4) - params["dig_t1"])) >> 12) * params["dig_t3"]) >> 14
        t_fine = var1 + var2
        return (t_fine * 5 + 128) >> 8

    def convert_pressure(self, raw_pressure, raw_temp):
        params = self.calib_params
        t_fine = self.convert_temp(raw_temp)
        var1 = ((t_fine >> 1) - 64000)
        var2 = (((var1 >> 2) * (var1 >> 2)) >> 11) * params["dig_p6"]
        var2 += ((var1 * params["dig_p5"]) << 1)
        var2 = (var2 >> 2) + (params["dig_p4"] << 16)
        var1 = (((params["dig_p3"] * ((var1 >> 2) * (var1 >> 2)) >> 13) >> 3) + ((params["dig_p2"] * var1) >> 1)) >> 18
        var1 = ((32768 + var1) * params["dig_p1"]) >> 15
        if var1 == 0:
            return 0
        p = ((1048576 - raw_pressure) - (var2 >> 12)) * 3125
        p = (p // var1) * 2
        var1 = (params["dig_p9"] * ((p >> 3) * (p >> 3)) >> 13) >> 12
        var2 = ((p >> 2) * params["dig_p8"]) >> 13
        p += (var1 + var2 + params["dig_p7"]) >> 4
        return p / 100.0
