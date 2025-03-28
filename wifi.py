import network
import time

# Configuración de la red Wi-Fi
SSID = "TP-Link_CC10"  # Reemplaza con tu SSID
PASSWORD = "18367638"  # Reemplaza con tu contraseña

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)  # Activa la interfaz Wi-Fi
    print("Conectando a Wi-Fi...")
    wlan.connect(SSID, PASSWORD)
    
    # Esperar conexión
    timeout = 10  # Tiempo de espera en segundos
    for _ in range(timeout):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)
    
    # Verificar la conexión
    if wlan.isconnected():
        print("\nConectado a Wi-Fi")
        #print("Dirección IP:", wlan.ifconfig()[0])
        return True
    else:
        print("\nError: No se pudo conectar a Wi-Fi")
        return False
