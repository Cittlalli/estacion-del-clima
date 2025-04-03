import uasyncio as asyncio
import machine
from machine import Pin, I2C
import wifi
from sensores.dht_sensor import DHT11
from sensores.bmp280_sensor import BMP280
import gc
import time
import _thread
import sd_logger  # Importar el módulo para la SD

# Configuración de pines
DHT_PIN_NUM = 28          # Pin del DHT11
I2C_SDA_PIN = 4           # Pin SDA para el BMP280
I2C_SCL_PIN = 5           # Pin SCL para el BMP280
LED_PIN = "LED"           # LED integrado

# Pines de la tarjeta SD (SPI)
SD_SCK_PIN = 6
SD_MOSI_PIN = 7
SD_MISO_PIN = 8
SD_CS_PIN = 9

# Inicializar la tarjeta SD con los pines configurados
sd_logger.sd_init(sck_pin=SD_SCK_PIN, mosi_pin=SD_MOSI_PIN, miso_pin=SD_MISO_PIN, cs_pin=SD_CS_PIN)

# Función para leer los datos previos de la SD
def leer_datos_sd():
    try:
        # Intenta leer datos previos o archivos guardados
        data = sd_logger.leer_datos()
        if data:
            print(f"📜 Datos previos leídos: {data}")
        else:
            print("No se encontraron datos previos.")
    except Exception as e:
        print(f"Error al leer los datos de la SD: {e}")

# Instanciar sensores
dht_sensor_obj = DHT11(Pin(DHT_PIN_NUM))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
bmp_sensor_obj = BMP280(i2c=i2c)

# Variables globales para almacenar lecturas actuales y últimas guardadas
dht_data = None      # (temperature, humidity)
bmp_data = None      # (temperature, pressure)
last_saved_data = None  # Últimos datos guardados

# Tarea para el LED
def led_task():
    led = Pin(LED_PIN, Pin.OUT)
    time.sleep(5)
    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

# Función para guardar datos solo cuando ambos sensores tienen lecturas nuevas
def verificar_y_guardar():
    global dht_data, bmp_data, last_saved_data

    if dht_data and bmp_data:
        temp_dht, hum_dht = dht_data
        temp_bmp, pres_bmp = bmp_data
        current_data = (temp_dht, hum_dht, temp_bmp, pres_bmp)

        # Guardar solo si los datos cambiaron
        if last_saved_data is None or last_saved_data != current_data:
            print(f"✅ Guardando datos -> Temp DHT11: {temp_dht}°C, Humedad: {hum_dht}%, Temp BMP280: {temp_bmp}°C, Presión: {pres_bmp} Pa")
            
            # Guardar en SD
            sd_logger.guardar_datos(temp_dht, hum_dht, pres_bmp)
            
            # Actualizar última lectura guardada
            last_saved_data = current_data

# Tareas para sensores (asíncronas)
async def dht_task():
    global dht_data
    while True:
        try:
            dht_sensor_obj.measure()
            dht_data = (dht_sensor_obj.temperature, dht_sensor_obj.humidity)
            print(f"DHT11 -> Temp: {dht_data[0]}°C, Hum: {dht_data[1]}%")
            
            # Intentar guardar si ya tenemos datos del BMP280
            verificar_y_guardar()
        except Exception as e:
            print("Error en DHT11:", e)
        await asyncio.sleep(15)

async def bmp_task():
    global bmp_data
    while True:
        try:
            raw_temp, raw_pressure = bmp_sensor_obj.read_raw_data()
            temp = bmp_sensor_obj.convert_temp(raw_temp) / 100.0
            pressure = bmp_sensor_obj.convert_pressure(raw_pressure, raw_temp)
            bmp_data = (temp, pressure)
            print(f"BMP280 -> Temp: {bmp_data[0]}°C, Presión: {bmp_data[1]} Pa")
            
            # Intentar guardar si ya tenemos datos del DHT11
            verificar_y_guardar()
        except Exception as e:
            print("Error en BMP280:", e)
        await asyncio.sleep(15)

# Función para iniciar la conexión Wi-Fi y tareas
async def main():
    # Iniciar la conexión Wi-Fi
    while not wifi.connect_wifi():
        await asyncio.sleep(1)

    # Crear tareas asíncronas
    asyncio.create_task(dht_task())
    asyncio.create_task(bmp_task())
    
    while True:
        await asyncio.sleep(1)

# Crear un hilo para el LED (sincronización con asyncio)
def start_led_thread():
    _thread.start_new_thread(led_task, ())

# Ejecutar el loop principal
if __name__ == "__main__":
    # Leer los datos de la SD al inicio
    leer_datos_sd()
    
    # Iniciar el hilo para el LED
    start_led_thread()
    
    # Ejecutar la parte asincrónica para sensores y ThingSpeak
    asyncio.run(main())
