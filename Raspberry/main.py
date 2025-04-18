import uasyncio as asyncio
import machine
from machine import Pin, I2C
import _thread
import time
import json
import ssd1306

from clima import determinar_condiciones_climaticas
from sensors import DHT11, BMP280
from comunicacion import connect_wifi, iniciar_servidor_websocket, send_message_to_all, get_conexion_ws
from sd_logger import SDLogger
from display import mostrar_datos

# Pines sesores
DHT_PIN_NUM = 28  # Pin de lectura del sensor DHT11
BMP_I2C_SDA_PIN = 4  # Pin SDA del bus I2C
BMP_I2C_SCL_PIN = 5  # Pin SCL del bus I2C

#Pines SD
SD_SPI_ID     = 0
SD_SCK_PIN = 18         # Pin SCK para SD AMARILLO
SD_MOSI_PIN = 19        # Pin MOSI para SD VERDE
SD_MISO_PIN = 16       # Pin MISO para SD MORADO
SD_CS_PIN = 17         # Pin CS (chip select) para SD AZUL

#Pines OLED
OLED_I2C_SDA_PIN = 2
OLED_I2C_SCL_PIN = 3

# Instanciar sensores
dht_sensor_obj = DHT11(Pin(DHT_PIN_NUM))  # Crear objeto para el sensor DHT11
i2c0 = I2C(0, scl=Pin(BMP_I2C_SCL_PIN), sda=Pin(BMP_I2C_SDA_PIN))  # Inicializar bus I2C
bmp_sensor_obj = BMP280(i2c=i2c0)  # Crear objeto para el sensor BMP280

#Instaciar pantalla OLED
i2c1= I2C(1, scl=Pin(OLED_I2C_SCL_PIN), sda=Pin(OLED_I2C_SDA_PIN))
oled = ssd1306.SSD1306_I2C(128, 64, i2c1)

# Instanciar logger SD
sd_logger = SDLogger(SD_SPI_ID, SD_SCK_PIN, SD_MOSI_PIN, SD_MISO_PIN, SD_CS_PIN)
try:
    sd_logger.init_sd()
except Exception:
    print("⚠️ No se pudo montar la SD al inicio. El sistema seguirá funcionando.")

# Variables 
dht_data = [None, None]
bmp_data = [None, None]
conexion_ws_activa = None
wifi = None
condicion_actual = None
last_data = {"temp": None, "hum": None, "pres": None}
last_condicion = "desconocido"
last_flags = {
    "enviando": False,
    "conectado": False,
    "guardando": False
}
presion_anterior = None

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
async def task_log_and_send():
    """
    Envía datos sólo si hubo un cambio o pasaron 10 min.
    También guarda en SD si hubo cambio drástico o pasaron 10 min.
    """
    
    global last_data, last_condicion, last_flags
    
    # Esperar a que wifi esté conectado
    while not wifi:
        await asyncio.sleep(1)

    last_sent = time.time()
    last_logged = time.time()

    while True:
        try:
            # --- EXTRACCIÓN SEGURA DE DATOS ---
            try:
                temp_raw = bmp_data[0]
                pres_raw = bmp_data[1]
            except (TypeError, IndexError):
                temp_raw = pres_raw = None
                print("⚠️ Datos BMP inválidos:", bmp_data)

            try:
                hum_raw = dht_data[1]
            except (TypeError, IndexError):
                hum_raw = None
                print("⚠️ Datos DHT inválidos:", dht_data)

            # --- CONVERSIÓN Y VALIDACIÓN ---
            temp = round(temp_raw, 2) if temp_raw is not None else None
            hum  = round(hum_raw,   2) if hum_raw  is not None else None
            pres = round(pres_raw,  2) if pres_raw is not None else None

            # Si falta cualquiera, esperamos y volvemos a intentar
            if None in (temp, hum, pres):
                await asyncio.sleep(5)
                continue
            
            cond = determinar_condiciones_climaticas(temp, hum, pres, presion_anterior=presion_anterior)

            # cálculo de cambios y tiempos
            cambios = (
                abs(temp - (last_data["temp"] or 0)) > 0.5 or
                abs(hum  - (last_data["hum"]  or 0)) > 2.0 or
                abs(pres - (last_data["pres"] or 0)) > 10.0
            )
            ahora = time.time()
            env_flag = cambios or (ahora - last_sent >= 60)
            log_flag = cambios or (ahora - last_logged >= 60)

            # Envío
            if env_flag:
                await send_message_to_all(json.dumps({
                    "temperatura": temp,
                    "humedad":    hum,
                    "presion":    pres,
                    "condicion":  cond
                }))
                last_sent = ahora

            # SD
            if log_flag:
                if not sd_logger.sd_montada:
                    sd_logger.intentar_reconexion()
                if sd_logger.sd_montada:
                    sd_logger.log_data(temp, pres, hum)
                    last_logged = ahora
                presion_anterior = pres

            # ——— Actualizamos las globales ———
            last_data["temp"]  = temp
            last_data["hum"]   = hum
            last_data["pres"]  = pres
            last_condicion     = cond
            last_flags["enviando"]   = env_flag
            last_flags["conectado"]  = wifi
            last_flags["guardando"]  = sd_logger.sd_montada

        except Exception as e:
            print("❌ Error en task_log_and_send:", e)

        await asyncio.sleep(5)

async def task_display():
    """
    Muestra en pantalla OLED los últimos valores de temp/hum/pres/condición.
    """
    while True:
        try:
            mostrar_datos(
                oled,
                last_data["temp"],
                last_data["hum"],
                last_data["pres"],
                condicion=last_condicion,
                enviando=bool(get_conexion_ws()),
                conectado=last_flags["conectado"],
                guardando=last_flags["guardando"]
            )
        except Exception as e:
            print("❌ Error en task_display:", e)
        await asyncio.sleep(5)

# Función principal
async def main():
    """
    Función principal que inicializa la conexión Wi-Fi, el servidor WebSocket y las tareas asíncronas
    para la lectura de sensores y el envío de datos.
    """
    global conexion_ws_activa
    global wifi

    wifi = connect_wifi()  # Intentar conectar a Wi-Fi hasta tener éxit
    
    # Leer y transformar el último dato de la SD
    ultimo_mensaje = None
    if sd_logger.sd_montada:
        try:
            dato = sd_logger.leer_ultimo_dato() 
            if dato:
                partes = dato.strip().split(",")
                if len(partes) == 4:
                    temp = float(partes[1])
                    pres = float(partes[2])
                    presion_anterior = pres
                    hum = float(partes[3])
                    condi = determinar_condiciones_climaticas(temp, hum, pres)
                    ultimo_mensaje = json.dumps({
                        "temperatura": temp,
                        "humedad": hum,
                        "presion": pres,
                        "condicion": condi
                    })
                else:
                    ultimo_mensaje = None
            else:
                ultimo_mensaje = None
        except Exception as e:
            print("⚠️ No se pudo formatear último mensaje:", e)
            ultimo_mensaje = None
        
    # Crear tareas asíncronas
    asyncio.create_task(iniciar_servidor_websocket(ultimo_mensaje))
    asyncio.create_task(task_display())
    asyncio.create_task(dht_task())
    asyncio.create_task(bmp_task())
    await asyncio.sleep(10)  # Esperar 10 segundos para que los sensores se estabilicen
    asyncio.create_task(task_log_and_send())

    # Bucle infinito para mantener las tareas en ejecución
    while True:
        await asyncio.sleep(1)

# Ejecutar el código asíncrono
asyncio.run(main())
