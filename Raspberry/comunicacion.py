import network
import time
import json
import socket
from clima import determinar_condiciones_climaticas

# Configuración de la red Wi-Fi
SSID = ""  # Reemplaza con tu SSID
PASSWORD = ""  # Reemplaza con tu contraseña

conexion_ws_activa = None 

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Conectando a Wi-Fi...")
    wlan.connect(SSID, PASSWORD)

    timeout = 10
    for _ in range(timeout):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(1)

    if wlan.isconnected():
        print("\nConectado a Wi-Fi")
        print("Dirección IP:", wlan.ifconfig()[0])
        return True
    else:
        print("\nError: No se pudo conectar a Wi-Fi")
        return False
    
def actualizar_datos_sensores(dht_data, bmp_data):
    global conexion_ws_activa
    if conexion_ws_activa:
        try:
            hum_dht = dht_data[1]
            temp_bmp, presion = bmp_data

            condicion = determinar_condiciones_climaticas(temp_bmp, hum_dht, presion)

            mensaje = json.dumps({
                "temperatura": temp_bmp,
                "humedad": hum_dht,
                "presion": presion,
                "condicion": condicion
            })

            send_ws_message(conexion_ws_activa, mensaje)
        except Exception as e:
            print("❌ Error al enviar datos:", e)

def handle_client(conn, dht_data, bmp_data):
    global conexion_ws_activa
    print("🔌 Cliente conectado.")
    try:
        data = conn.recv(1024)
        if b"Upgrade: websocket" in data:
            # Handshake
            import ubinascii
            import hashlib

            key = ""
            for line in data.decode().split("\r\n"):
                if "Sec-WebSocket-Key" in line:
                    key = line.split(": ")[1]
                    break

            GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            hash = hashlib.sha1((key + GUID).encode())
            response_key = ubinascii.b2a_base64(hash.digest()).decode().strip()

            handshake = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {response_key}\r\n\r\n"
            )
            conn.send(handshake.encode())
            conexion_ws_activa = conn 

            while True:
                time.sleep(1)  
    except Exception as e:
        print("❌ Error en conexión:", e)
    finally:
        conn.close()

def send_ws_message(conn, message):
    payload = message.encode("utf-8")
    header = bytearray()

    header.append(0x81)  
    length = len(payload)
    if length < 126:
        header.append(length)
    elif length < (1 << 16):
        header.append(126)
        header.extend(length.to_bytes(2, "big"))
    else:
        header.append(127)
        header.extend(length.to_bytes(8, "big"))

    conn.send(header + payload)

def iniciar_servidor_websocket(puerto=8765, dht_data=None, bmp_data=None):
    print(f"🌐 WebSocket en puerto {puerto}...")
    addr = socket.getaddrinfo("0.0.0.0", puerto)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Esperando conexiones...")

    while True:
        conn, addr = s.accept()
        print("📡 Cliente conectado desde", addr)
        handle_client(conn, dht_data, bmp_data)
