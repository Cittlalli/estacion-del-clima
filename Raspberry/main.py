"""
Sistema IoT para monitoreo ambiental basado en el BME280,
con visualización en pantalla OLED, almacenamiento en SD, 
y comunicación mediante WebSocket.

Este script:
- Lee datos ambientales (temperatura, humedad, presión) desde un sensor BME280.
- Los muestra en una pantalla OLED.
- Los almacena periódicamente en una tarjeta SD.
- Los envía en tiempo real mediante WebSocket.
- Sincroniza la hora vía NTP y administra la conectividad Wi-Fi.

Dependencias:
    - machine (I2C, Pin)
    - uasyncio
    - time, ntptime
    - ssd1306
    - ujson, os
    - clima, sensors, comunicacion, sd_logger, display (módulos personalizados)
"""

import uasyncio as asyncio
import time
from machine import Pin, I2C
import ssd1306
import ntptime
import ujson as json
import os

from clima import determinar_condiciones_climaticas
from sensors import BME280
from comunicacion import WiFiManager, WebSocketServer
from sd_logger import SDLogger
from display import mostrar_datos, mostrar_logo

# Pines sensores
BME_I2C_SDA_PIN = 26
BME_I2C_SCL_PIN = 27

# Pines SD
SD_SPI_ID = 0
SD_SCK_PIN = 18
SD_MOSI_PIN = 19
SD_MISO_PIN = 16
SD_CS_PIN = 17

# Pines OLED
OLED_I2C_SDA_PIN = 2
OLED_I2C_SCL_PIN = 3

DEBUG = True
def debug(*args):
    """
    Imprime mensajes de depuración si `DEBUG` está activado.
    Args:
        *args: Mensajes a imprimir.
    """
    if DEBUG:
        print("[DEBUG][MAIN]", *args)

# Instanciar hardware
debug("🛠️ Inicializando sensores y pantallas")
i2c0 = I2C(0, scl=Pin(BME_I2C_SCL_PIN), sda=Pin(BME_I2C_SDA_PIN))
bme = BME280.BME280(i2c=i2c0)
i2c1 = I2C(1, scl=Pin(OLED_I2C_SCL_PIN), sda=Pin(OLED_I2C_SDA_PIN))
oled = ssd1306.SSD1306_I2C(128, 64, i2c1)

# Logger SD
sd_logger = SDLogger(SD_SPI_ID, SD_SCK_PIN, SD_MOSI_PIN, SD_MISO_PIN, SD_CS_PIN)

# Conectividad
wifi = WiFiManager()
ws_server = WebSocketServer(sd_logger)

# Estados globales
last_data = {"temp": None, "hum": None, "pres": None}
ultimo_mensaje = None
last_send_time = 0
last_hist_time = 0
last_slog_time = 0
presion_anterior = None

# Sincronizar hora vía NTP
async def sync_ntp():
    """
    Sincroniza la hora del sistema con un servidor NTP.
    Reintenta hasta 5 veces si hay conexión Wi-Fi.
    """
    for _ in range(5):
        if wifi.is_connected():
            try:
                ntptime.settime()
                debug("🕒 Hora sincronizada con NTP")
                return
            except Exception as e:
                debug("⚠️ Error al sincronizar NTP:", e)
        await asyncio.sleep(2)
    debug("❌ No se pudo sincronizar NTP tras varios intentos")

# Lectura BME280
async def bme_task():
    """
    Tarea asíncrona que lee periódicamente los datos del sensor BME280.
    Actualiza la variable global `last_data` cada 15 segundos.
    """
    while True:
        try:
            last_data["temp"] = bme.temperature
            last_data["hum"] = bme.humidity
            last_data["pres"] = bme.pressure
            debug(f"🌡️ Temp: {last_data['temp']}°C | 🧭 Pres: {last_data['pres']} hPa")
        except Exception as e:
            debug("⚠️ Error al leer BMP280:", e)
        await asyncio.sleep(15)

# Gestión Wi-Fi y servidor
async def task_connectivity():
    """
    Administra la conectividad Wi-Fi y la inicialización del servidor WebSocket.
    Intenta reconectar si se pierde la conexión y reinicia el servidor WebSocket si no está activo.
    """
    while True:
        if not wifi.is_connected():
            debug("📡 Intentando conectar Wi-Fi...")
            wifi.connect()
            if wifi.is_connected():
                debug(f"Conectado correctamente. IP: {wifi.get_ip()}")
                await sync_ntp()
                ws_server.start(ultimo_mensaje)
        else:
            await asyncio.sleep(10)
            if not ws_server.running:
                debug("🔁 Reiniciando WebSocket Server")
                ws_server.start(ultimo_mensaje)
        if wifi.lost_connection():
            debug("❌ Wi-Fi desconectado")
            ws_server.stop()
        await asyncio.sleep(3)

# Mostrar en OLED
async def task_display():
    """
    Muestra los datos en una pantalla OLED.

    Si los datos aún no están disponibles, muestra un logo de espera.
    Una vez disponibles, se actualiza con datos ambientales y estado del sistema.
    """
    showed_logo = False
    while True:
        ws_server.update_flags(sd_logger.sd_montada)
        if None in last_data.values():
            if not showed_logo:
                debug("🖼️ Mostrando logo de espera en OLED")
                mostrar_logo(oled)
                showed_logo = True
        else:
            cond = determinar_condiciones_climaticas(
                last_data["temp"], last_data["hum"], last_data["pres"], presion_anterior=presion_anterior
            )
            debug(f"📺 Mostrando OLED: {last_data['temp']}°C, {last_data['hum']}%, {last_data['pres']}hPa, Cond: {cond}")
            mostrar_datos(
                oled,
                last_data["temp"], last_data["hum"], last_data["pres"],
                cond,
                enviando=ws_server.flags['enviando'],
                conectado=ws_server.flags['conectado'],
                guardando=ws_server.flags['guardando']
            )
            showed_logo = False
        await asyncio.sleep(5)

# Log y envío de datos/historial
async def task_log_and_send():
    """
    Tarea principal de manejo de datos:
        - Envía datos actuales cada 60 segundos por WebSocket.
        - Envía el historial cada 60 segundos si hay conexión WebSocket.
        - Guarda en la SD cada 10 minutos si está montada.
        - Actualiza `ultimo_mensaje` y `presion_anterior`.
    """
    global ultimo_mensaje, last_send_time, last_slog_time, last_hist_time, presion_anterior
    while not wifi.is_connected():
        await asyncio.sleep(1)
    while True:
        now = time.time()
        ws_server.update_flags(sd_logger.sd_montada)

        if None in last_data.values():
            await asyncio.sleep(5)
            continue

        cond = determinar_condiciones_climaticas(
            last_data["temp"], last_data["hum"], last_data["pres"], presion_anterior=presion_anterior
        )
        msg = {
            "temperatura": last_data["temp"],
            "humedad": last_data["hum"],
            "presion": last_data["pres"],
            "condicion": cond
        }
        ultimo_mensaje = msg

        if ws_server.connections:
            if now - last_send_time >= 60:
                debug("📤 Enviando datos actuales por WebSocket")
                await ws_server.handle_sending(data=msg, send_history=False)
                last_send_time = now

            if now - last_hist_time >= 60:
                debug("📦 Enviando historial por WebSocket")
                await ws_server.handle_sending(data=None, send_history=True)
                last_hist_time = now

        if sd_logger.sd_montada and now - last_slog_time >= 600:
            debug("💾 Guardando en SD")
            sd_logger.log_data(
                last_data["temp"], last_data["pres"], last_data["hum"]
            )
            last_slog_time = now

        presion_anterior = last_data["pres"]
        await asyncio.sleep(5)

async def main():
    """
    Función principal que inicializa componentes, monta la SD y lanza las tareas asíncronas del sistema.
    Verifica la existencia de la configuración Wi-Fi y carga el último dato guardado si está disponible.
    """
    global presion_anterior, ultimo_mensaje
    try:
        debug("💽 Intentando montar SD...")
        sd_logger.init_sd()
        debug("✅ SD montada correctamente")
        d = sd_logger.leer_ultimo_dato()
        if d:
            parts = d.strip().split(',')
            if len(parts) == 4:
                temp, pres, hum = map(float, parts[1:4])
                presion_anterior = pres
                cond0 = determinar_condiciones_climaticas(temp, hum, pres)
                ultimo_mensaje = {"temperatura": temp, "humedad": hum, "presion": pres, "condicion": cond0}
                debug(f"🔁 Último dato cargado: {ultimo_mensaje}")
    except Exception as e:
        debug("⚠️ Error al inicializar SD o leer datos:", e)

    if "wifi_config.json" not in os.listdir('/'):
        debug("📁 Creando plantilla wifi_config.json")
        with open('/wifi_config.json', 'w') as f:
            json.dump({"networks": [], "static": {}}, f)

    debug("🚀 Iniciando tareas asincrónicas")
    asyncio.create_task(task_display())
    await asyncio.sleep(3)
    asyncio.create_task(task_connectivity())
    asyncio.create_task(bme_task())
    asyncio.create_task(task_log_and_send())

    while True:
        await asyncio.sleep(1)

debug("🧠 Ejecutando main()")
asyncio.run(main())
