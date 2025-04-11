import network
import time
import json
import socket
import uasyncio as asyncio
import ubinascii
import hashlib

# Credenciales de red Wi-Fi
SSID = ""
PASSWORD = ""

# Lista global para gestionar conexiones WebSocket activas
conexion_ws_activa = []

def set_conexion_ws(conn):
    """
    Agrega una conexión WebSocket a la lista si no está ya incluida.

    :param conn: Objeto de conexión del cliente WebSocket.
    """
    if conn not in conexion_ws_activa:
        conexion_ws_activa.append(conn)

def remove_conexion_ws(conn):
    """
    Elimina una conexión WebSocket de la lista si existe.

    :param conn: Objeto de conexión del cliente WebSocket.
    """
    if conn in conexion_ws_activa:
        conexion_ws_activa.remove(conn)

def get_conexion_ws():
    """
    Devuelve la lista actual de conexiones WebSocket activas.

    :return: Lista de conexiones WebSocket.
    """
    return conexion_ws_activa

def connect_wifi():
    """
    Intenta conectar el dispositivo a la red Wi-Fi definida por SSID y PASSWORD.

    :return: True si se conecta exitosamente, False en caso contrario.
    """
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

async def iniciar_servidor_websocket():
    """
    Inicia un servidor WebSocket en el puerto 8765 que acepta múltiples conexiones entrantes.
    """
    print(f"🌐 WebSocket en puerto 8765...")
    addr = socket.getaddrinfo("0.0.0.0", 8765)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    s.setblocking(False)
    print("Esperando conexiones...")

    while True:
        try:
            # Acepta nuevas conexiones no bloqueantes
            conn, addr = await asyncio.sleep_ms(0) or s.accept()
            conn.setblocking(True)
            print("📡 Cliente conectado desde", addr)
            asyncio.create_task(handle_client(conn))
        except:
            await asyncio.sleep(0.1)

async def handle_client(conn):
    """
    Maneja la conexión de un cliente WebSocket realizando el handshake y gestionando la conexión.

    :param conn: Objeto de conexión del cliente.
    """
    try:
        # Realiza el handshake WebSocket
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
    except Exception as e:
        print("❌ Error al hacer handshake:", e)
        return

    try:
        # Mantiene la conexión activa
        while True:
            await asyncio.sleep(5)
    except Exception as e:
        print("🔌 Cliente desconectado:", e)
    finally:
        # Cierra y elimina la conexión
        remove_conexion_ws(conn)
        conn.close()
        print("🧹 Conexión cerrada y removida")

def send_ws_message(conn, message):
    """
    Envía un mensaje a un cliente WebSocket con el protocolo adecuado.

    :param conn: Conexión del cliente WebSocket.
    :param message: Mensaje a enviar en formato string.
    """
    try:
        payload = message.encode("utf-8")
        header = bytearray()
        header.append(0x81)  # Frame tipo texto, FIN

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
        remove_conexion_ws(conn)
        conn.close()

async def send_message_to_all(message):
    """
    Envía un mensaje a todos los clientes WebSocket conectados.

    :param message: Texto del mensaje a enviar.
    """
    for conn in list(conexion_ws_activa):
        send_ws_message(conn, message)
        await asyncio.sleep(0)
