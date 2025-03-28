import uasyncio as asyncio
import machine
from machine import Pin, I2C
import wifi
from dht_sensor import DHT11
from bmp280_sensor import BMP280
import thingspeak
import gc
import time
import _thread

# Configuración de pines
DHT_PIN_NUM = 28          # Pin del DHT11
I2C_SDA_PIN = 4           # Pin SDA para el BMP280
I2C_SCL_PIN = 5           # Pin SCL para el BMP280
LED_PIN = "LED"            # LED integrado

# Instanciar sensores
dht_sensor_obj = DHT11(Pin(DHT_PIN_NUM))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
bmp_sensor_obj = BMP280(i2c=i2c)

# Variables globales para almacenar lecturas
dht_data = None   # (temperature, humidity)
bmp_data = None   # (temperature, pressure)

# Tarea para el LED
def led_task():
    led = Pin(LED_PIN, Pin.OUT)
    time.sleep(5)
    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

# Tareas para sensores y ThingSpeak (asíncronas)
async def dht_task():
    global dht_data
    while True:
        try:
            dht_sensor_obj.measure()
            dht_data = (dht_sensor_obj.temperature, dht_sensor_obj.humidity)
            print("DHT11 -> Temp: {}°C, Hum: {}%".format(*dht_data))
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
            print("BMP280 -> Temp: {}°C, Pressure: {} hPa".format(temp, pressure))
        except Exception as e:
            print("Error en BMP280:", e)
        await asyncio.sleep(15)

async def thingspeak_task():
    global dht_data, bmp_data
    while True:
        if dht_data is not None and bmp_data is not None:
            temp, hum = dht_data
            _, pressure = bmp_data
            thingspeak.thingspeak_send(temp, hum, pressure)
            # Reiniciar datos (opcional)
            dht_data, bmp_data = None, None
            gc.collect()
        await asyncio.sleep(15)

# Función para iniciar la conexión Wi-Fi y tareas
async def main():
    # Iniciar la conexión Wi-Fi
    while not wifi.connect_wifi():
        await asyncio.sleep(1)

    # Crear tareas asíncronas para sensores y ThingSpeak
    asyncio.create_task(dht_task())
    asyncio.create_task(bmp_task())
    asyncio.create_task(thingspeak_task())
    
    while True:
        await asyncio.sleep(1)

# Crear un hilo para el LED (sincronización con asyncio)
def start_led_thread():
    _thread.start_new_thread(led_task, ())

# Ejecutar el loop principal
if __name__ == "__main__":
    # Iniciar el hilo para el LED
    start_led_thread()
    
    # Ejecutar la parte asincrónica para sensores y ThingSpeak
    asyncio.run(main())
