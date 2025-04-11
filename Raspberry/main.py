import uasyncio as asyncio
import machine
from machine import Pin, I2C
import _thread
import time
import json

from clima import determinar_condiciones_climaticas
from sensors import DHT11, BMP280
from comunicacion import connect_wifi, iniciar_servidor_websocket, send_message_to_all, get_conexion_ws

# Pines
DHT_PIN_NUM = 28  # Pin de lectura del sensor DHT11
I2C_SDA_PIN = 4  # Pin SDA del bus I2C
I2C_SCL_PIN = 5  # Pin SCL del bus I2C

# Instanciar sensores
dht_sensor_obj = DHT11(Pin(DHT_PIN_NUM))  # Crear objeto para el sensor DHT11
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))  # Inicializar bus I2C
bmp_sensor_obj = BMP280(i2c=i2c)  # Crear objeto para el sensor BMP280

# Variables para guardar los últimos datos leídos
dht_data = [None, None]  # Almacena temperatura y humedad de DHT11
bmp_data = [None, None]  # Almacena temperatura y presión de BMP280
conexion_ws_activa = None  # Variable para las conexiones WebSocket activas

# Tarea asíncrona para leer datos del sensor DHT11
async def dht_task():
    """
    Tarea asíncrona que mide la temperatura y humedad del sensor DHT11 cada 15 segundos.
    Actualiza las variables dht_data con los últimos valores leídos.
    """
    global dht_data
    while True:
        try:
            dht_sensor_obj.measure()  # Realizar medición
            dht_data = (dht_sensor_obj.temperature, dht_sensor_obj.humidity)  # Guardar datos
            print(f"DHT11 -> Temperatura:{dht_data[0]}°C Humedad: {dht_data[1]}%")
        except Exception as e:
            print("Error DHT11:", e)  # Manejo de errores en la lectura
        await asyncio.sleep(15)  # Esperar 15 segundos antes de la siguiente medición

# Tarea asíncrona para leer datos del sensor BMP280
async def bmp_task():
    """
    Tarea asíncrona que lee la temperatura y presión del sensor BMP280 cada 15 segundos.
    Actualiza las variables bmp_data con los últimos valores leídos.
    """
    global bmp_data
    while True:
        try:
            raw_temp, raw_pressure = bmp_sensor_obj.read_raw_data()  # Leer datos crudos
            temp = bmp_sensor_obj.convert_temp(raw_temp) / 100.0  # Convertir temperatura
            pressure = bmp_sensor_obj.convert_pressure(raw_pressure, raw_temp)  # Convertir presión
            bmp_data = (temp, pressure)  # Guardar datos
            print(f"BMP280 -> Temp: {temp}°C, Presión: {pressure} Pa")
        except Exception as e:
            print("Error BMP280:", e)  # Manejo de errores en la lectura
        await asyncio.sleep(15)  # Esperar 15 segundos antes de la siguiente medición

# Tarea asíncrona para enviar los datos a través de WebSocket
async def task_envio_datos():
    """
    Tarea asíncrona que envía los datos de los sensores a todos los clientes WebSocket conectados
    cada 10 segundos si los datos están disponibles y las conexiones están activas.
    """
    while True:
        conexiones = get_conexion_ws()  # Obtener las conexiones WebSocket activas
        print(f"📡 Conexiones activas: {len(conexiones)}" if conexiones else "📡 Sin conexiones WebSocket")
        print("📦 DHT:", dht_data, "| BMP:", bmp_data)  # Imprimir los datos
        if (
            dht_data[0] is not None and  # Verificar que los datos de DHT11 no sean None
            bmp_data[0] is not None and  # Verificar que los datos de BMP280 no sean None
            isinstance(get_conexion_ws(), list) and  # Asegurar que la variable de conexiones es una lista
            len(get_conexion_ws()) > 0  # Asegurar que haya al menos una conexión WebSocket
        ):
            try:
                hum_dht = dht_data[1]  # Obtener la humedad de DHT11
                temp_bmp, presion = bmp_data  # Obtener la temperatura y presión de BMP280
                mensaje = json.dumps({
                    "temperatura": temp_bmp,
                    "humedad": hum_dht,
                    "presion": presion,
                    "condicion": determinar_condiciones_climaticas(temp_bmp, hum_dht, presion)  # Determinar condición climática
                })
                await send_message_to_all(mensaje)  # Enviar el mensaje a todos los clientes conectados
            except Exception as e:
                print("❌ Error al enviar datos:", e)  # Manejo de errores al enviar datos
        await asyncio.sleep(10)  # Esperar 10 segundos antes de enviar los datos nuevamente

# Función principal
async def main():
    """
    Función principal que inicializa la conexión Wi-Fi, el servidor WebSocket y las tareas asíncronas
    para la lectura de sensores y el envío de datos.
    """
    global conexion_ws_activa

    while not connect_wifi():  # Intentar conectar a Wi-Fi hasta tener éxito
        print("Conectando a Wi-Fi...")
        await asyncio.sleep(1)
    
    # Crear tareas asíncronas
    asyncio.create_task(iniciar_servidor_websocket())
    asyncio.create_task(dht_task())
    asyncio.create_task(bmp_task())
    await asyncio.sleep(10)  # Esperar 10 segundos para que los sensores se estabilicen
    asyncio.create_task(task_envio_datos())

    # Bucle infinito para mantener las tareas en ejecución
    while True:
        await asyncio.sleep(1)

# Ejecutar el código asíncrono
asyncio.run(main())
