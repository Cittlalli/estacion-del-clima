# comunicacion.py

import network
import time
import json
import socket
from clima import determinar_condiciones_climaticas
import ubinascii
import hashlib

# Wi-Fi
SSID = "TP-Link_CC10"
PASSWORD = "18367638"

conexion_ws_activa = None  # conexión websocket global

def set_conexion_ws(conn):
    global conexion_ws_activa
    conexion_ws_activa = conn


def get_conexion_ws():
    return conexion_ws_activa


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


def iniciar_servidor_websocket():
    print(f"🌐 WebSocket en puerto 8765...")
    addr = socket.getaddrinfo("0.0.0.0", 8765)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Esperando conexiones...")

    conn, addr = s.accept()
    print("📡 Cliente conectado desde", addr)

    try:
        data = conn.recv(1024)
        if b"Upgrade: websocket" in data:
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
            set_conexion_ws(conn)
            print("✅ Conexión WebSocket establecida.")
            return True
    except Exception as e:
        print("❌ Error en conexión:", e)

    return False


def send_ws_message(conn, message):
    try:
        payload = message.encode("utf-8")
        header = bytearray()
        header.append(0x81)  # texto, FIN = 1

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
        print(f"📤 Enviado: {message}")
    except Exception as e:
        print("❌ Error al enviar:", e)

