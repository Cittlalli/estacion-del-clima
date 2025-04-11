# main.py

import uasyncio as asyncio 
import machine
from machine import Pin, I2C
import _thread
import time
import json

from clima import determinar_condiciones_climaticas
from sensors import DHT11, BMP280
from comunicacion import connect_wifi, iniciar_servidor_websocket, send_ws_message, get_conexion_ws

# Pines
DHT_PIN_NUM = 28
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
LED_PIN = "LED"

# Instanciar sensores
dht_sensor_obj = DHT11(Pin(DHT_PIN_NUM))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
bmp_sensor_obj = BMP280(i2c=i2c)

# Variables para guardar los últimos datos leídos
dht_data = [None, None]
bmp_data = [None, None]
conexion_ws_activa = None  

# LED thread
def led_task():
    led = Pin(LED_PIN, Pin.OUT)
    while True:
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

# Tareas asíncronas para sensores
async def dht_task():
    global dht_data
    while True:
        try:
            dht_sensor_obj.measure()
            dht_data = (dht_sensor_obj.temperature, dht_sensor_obj.humidity)
            print(f"DHT11 -> Temperatura:{dht_data[0]}°C Humedad: {dht_data[1]}%")
        except Exception as e:
            print("Error DHT11:", e)
        await asyncio.sleep(15)

async def bmp_task():
    global bmp_data
    while True:
        try:
            raw_temp, raw_pressure = bmp_sensor_obj.read_raw_data()
            temp = bmp_sensor_obj.convert_temp(raw_temp) / 100.0
            pressure = bmp_sensor_obj.convert_pressure(raw_pressure, raw_temp)
            bmp_data = (temp, pressure)
            print(f"BMP280 -> Temp: {temp}°C, Presión: {pressure} Pa")
        except Exception as e:
            print("Error BMP280:", e)
        await asyncio.sleep(15)
        
async def task_envio_datos():
    conexion_ws_activa = get_conexion_ws()
    while True:
        print("📡 Estado conexión:", conexion_ws_activa)
        print("📦 DHT:", dht_data, "| BMP:", bmp_data)
        if dht_data[0] is not None and bmp_data[0] is not None and conexion_ws_activa:
            try:
                hum_dht = dht_data[1]
                temp_bmp, presion = bmp_data
                mensaje = json.dumps({
                    "temperatura": temp_bmp,
                    "humedad": hum_dht,
                    "presion": presion,
                    "condicion": determinar_condiciones_climaticas(temp_bmp, hum_dht, presion)
                })
                await send_ws_message(conexion_ws_activa, mensaje)
            except Exception as e:
                print("❌ Error al enviar datos:", e)
        await asyncio.sleep(10)

# Main principal
async def main():
    global conexion_ws_activa

    while not connect_wifi():
        print("Conectando a Wi-Fi...")
        await asyncio.sleep(1)
    
    while not iniciar_servidor_websocket():
        await asyncio.sleep(1)    
    asyncio.create_task(dht_task())
    asyncio.create_task(bmp_task())
    await asyncio.sleep(10)
    asyncio.create_task(task_envio_datos())

    while True:
        await asyncio.sleep(1)

# Ejecutar
_thread.start_new_thread(led_task, ())
asyncio.run(main())