import os
import sdcard
import machine

# Variables globales para la SD y RTC
spi = None
cs = None
sd = None
rtc = None

def sd_init(sck_pin, mosi_pin, miso_pin, cs_pin):
    """Inicializa la tarjeta SD y el RTC con los pines especificados."""
    global spi, cs, sd, rtc

    # Configurar SPI con los pines proporcionados
    spi = machine.SPI(1, baudrate=1000000, polarity=0, phase=0,
                      sck=machine.Pin(sck_pin), 
                      mosi=machine.Pin(mosi_pin), 
                      miso=machine.Pin(miso_pin))
    
    cs = machine.Pin(cs_pin, machine.Pin.OUT)
    sd = sdcard.SDCard(spi, cs)
    
    try:
        os.mount(sd, "/sd")
        print("✅ Tarjeta SD montada correctamente.")
    except Exception as e:
        print("⚠ Error al montar la tarjeta SD:", e)
    
    # Inicializar RTC
    rtc = machine.RTC()
    print("✅ RTC inicializado.")

def guardar_datos(temperatura, humedad, presion):
    """Guarda datos en un archivo CSV con fecha y hora actual."""
    if not rtc:
        print("⚠ Error: RTC no inicializado. Llama a sd_init() primero.")
        return
    
    # Obtener la fecha y hora actual al momento de la llamada
    anio, mes, dia, _, hora, minuto, segundo, _ = rtc.datetime()
    datos = f"{anio}-{mes:02d}-{dia:02d},{hora:02d}:{minuto:02d}:{segundo:02d},{temperatura},{humedad},{presion}\n"
    
    with open("/sd/datos_clima.csv", "a") as f:
        f.write(datos)
    
    print("💾 Datos guardados en SD:", datos.strip())

def leer_datos(fecha=None, hora_inicio=None, hora_fin=None):
    """Lee datos del archivo CSV y permite filtrar por fecha y rango de hora."""
    try:
        with open("/sd/datos_clima.csv", "r") as f:
            lineas = f.readlines()
        
        resultados = []
        for linea in lineas:
            partes = linea.strip().split(",")
            fecha_dato, hora_dato, temp, hum, pres = partes
            
            if fecha and fecha != fecha_dato:
                continue
            
            if hora_inicio and hora_fin:
                if not (hora_inicio <= hora_dato <= hora_fin):
                    continue
            
            resultados.append(linea.strip())
        
        return resultados

    except Exception as e:
        print("⚠ Error al leer los datos:", e)
        return []
