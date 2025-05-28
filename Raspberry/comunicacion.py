import network
import time
import socket
import hashlib
import ubinascii
import uasyncio as asyncio
import json
import os

# Archivo de configuración de Wi-Fi
default_config = {
    "networks": [
        { "ssid": "", "password": "" }
    ]
}

class WiFiManager:
    """
    Administra la conexión Wi-Fi en dispositivos compatibles con MicroPython.

    Lee la configuración desde un archivo JSON o usa valores por defecto.
    Intenta conectarse a una de las redes especificadas. Soporta configuración
    IP estática si está disponible en el archivo de configuración.
    """
    def __init__(self):
        """
        Inicializa el administrador Wi-Fi.
        """
        self.wlan = network.WLAN(network.STA_IF)
        self._was_connected = False
        self.retry_interval = None
        self.config = None
        self.static = None
        self.networks = None
        self.wlan.disconnect() 

    def _load_config(self, path):
        """
        Carga la configuración Wi-Fi desde un archivo JSON.

        Args:
            path (str): Ruta del archivo de configuración.

        Returns:
            dict: Configuración cargada o valores por defecto.
        """
        try:
            if path in os.listdir('/'):
                with open(path, 'r') as f:
                    return json.loads(f.read())
        except Exception:
            pass
        return default_config

    def connect(self, config_path="/wifi_config.json", retry_interval=5):
        """
        Intenta conectarse a las redes especificadas en el archivo de configuración.

        Args:
            config_path (str): Ruta del archivo de configuración Wi-Fi.
            retry_interval (int): Intervalo de reintento en segundos.

        Returns:
            bool: True si se conecta correctamente, False si falla.
        """
        self.retry_interval = retry_interval
        self.config = self._load_config(config_path)
        self.static = self.config.get('static')
        self.networks = self.config.get('networks', [])
        
        if not self.wlan.active():
            self.wlan.active(True)
        try:
            scan = [ssid.decode() for ssid, *_ in self.wlan.scan()]
        except Exception:
            scan = []
        for net in self.networks:
            ssid, pwd = net.get('ssid'), net.get('password')
            if ssid in scan or len(self.networks) == 1:
                self.wlan.connect(ssid, pwd)
                start = time.time()
                while time.time() - start < 15:
                    if self.wlan.isconnected(): break
                    time.sleep(1)
                if self.wlan.isconnected() and self.static:
                    try:
                        self.wlan.ifconfig((
                            self.static['ip'], self.static['subnet'],
                            self.static['gateway'], self.static['dns']
                        ))
                    except:
                        pass
                break
        self._was_connected = self.wlan.isconnected()
        return self._was_connected

    def is_connected(self):
        """
        Verifica si hay conexión Wi-Fi activa.

        Returns:
            bool: True si está conectado, False en caso contrario.
        """
        return self.wlan.isconnected()

    def lost_connection(self):
        """
        Detecta si se perdió la conexión desde el último estado.

        Returns:
            bool: True si se perdió la conexión, False si se mantiene.
        """
        now = self.wlan.isconnected()
        lost = self._was_connected and not now
        self._was_connected = now
        return lost

    def get_ip(self):
        """
        Obtiene la dirección IP actual.

        Returns:
            str: Dirección IP si está conectado, None en caso contrario.
        """
        if self.wlan.isconnected(): return self.wlan.ifconfig()[0]
        return None

class WebSocketServer:
    """
    Servidor WebSocket para envío de datos en tiempo real o historial desde almacenamiento SD.

    Permite conexiones WebSocket y transmite datos a múltiples clientes,
    distinguiendo entre conexiones de tipo 'real' (tiempo real) e 'historial'.
    """
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, sd_logger, port=8765):
        """
        Inicializa el servidor WebSocket.

        Args:
            sd_logger: Objeto con funcionalidad para leer desde almacenamiento SD.
            port (int): Puerto en el que el servidor escucha.
        """
        self.sd_logger = sd_logger
        self.port = port
        self.running = False
        self.server_task = None
        self.connections = {}
        self.flags = {'enviando': False, 'conectado': False, 'guardando': False}
        self.ultimo_mensaje = None

    def start(self, ultimo_mensaje=None):
        """
        Inicia el servidor WebSocket de forma asíncrona.

        Args:
            ultimo_mensaje (dict, optional): Último mensaje para enviar a nuevas conexiones.
        """
        if not self.running:
            self.ultimo_mensaje = ultimo_mensaje
            self.running = True
            self.flags['conectado'] = True
            self.server_task = asyncio.create_task(self._serve())

    def stop(self):
        """
        Detiene el servidor WebSocket y cierra todas las conexiones activas.
        """
        if self.running:
            self.running = False
            for conn in list(self.connections):
                try: conn.close()
                except: pass
            self.connections.clear()
            if self.server_task: self.server_task.cancel()
            self.flags['conectado'] = False

    async def _serve(self):
        """
        Bucle principal del servidor para aceptar y manejar conexiones entrantes.
        """
        addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr)
        sock.listen(5)
        sock.setblocking(False)
        while self.running:
            try:
                conn, _ = sock.accept()
                conn.setblocking(True)
                asyncio.create_task(self._handle_client(conn))
            except OSError:
                await asyncio.sleep(0.1)
        sock.close()

    async def _handle_client(self, conn):
        """
        Maneja el proceso de handshake y comunicación con un cliente WebSocket.

        Args:
            conn (socket): Conexión del cliente.
        """
        data = conn.recv(1024)
        if b"Upgrade: websocket" not in data:
            conn.close(); return
        key = next((line.split(': ')[1] for line in data.decode().split('\r\n') if line.startswith('Sec-WebSocket-Key:')), None)
        if not key:
            conn.close(); return
        accept = ubinascii.b2a_base64(hashlib.sha1((key + self.GUID).encode()).digest()).decode().strip()
        conn.send((
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {accept}\r\n\r\n'
        ).encode())

        # Tipo de conexión
        inicial = conn.recv(256)
        tipo = 'real'
        try:
            req = json.loads(inicial.decode())
            if req.get('solicitud') == 'historial': tipo = 'historial'
        except:
            pass
        self.connections[conn] = tipo

        # Envío inicial según tipo
        if tipo == 'real' and self.ultimo_mensaje:
            await self._send(conn, json.dumps(self.ultimo_mensaje))
        elif tipo == 'historial':
            historial = self._leer_historial_completo(10)
            await self._send(conn, json.dumps({'historial': historial}))

        try:
            while self.running:
                await asyncio.sleep(0.1)
        finally:
            conn.close()
            self.connections.pop(conn, None)

    async def handle_sending(self, data=None, send_history=False, history_count=10):
        """
        Envía datos a clientes conectados según el tipo de conexión.

        Args:
            data (dict, optional): Datos en tiempo real para enviar a tipo 'real'.
            send_history (bool): Si es True, reenvía historial a tipo 'historial'.
            history_count (int): Cantidad de registros del historial a enviar.
        """
        self.flags['enviando'] = False
        for conn, tipo in list(self.connections.items()):
            if tipo == 'real' and data is not None:
                await self._send(conn, json.dumps(data))
                self.flags['enviando'] = True
            if tipo == 'historial' and send_history:
                historial = self._leer_historial_completo(history_count)
                await self._send(conn, json.dumps({'historial': historial}))

    def _leer_historial_completo(self, cantidad):
        """
        Lee el historial completo desde los archivos de la tarjeta SD.

        Args:
            cantidad (int): Número de registros a leer.

        Returns:
            list: Lista de líneas del historial, o mensaje de error si no disponible.
        """
        if not self.sd_logger.sd_montada:
            return 'no disponible'
        archivos = [f for f in os.listdir(self.sd_logger.mount_point)
                    if f.startswith('lecturas_') and f.endswith('.csv')]
        archivos.sort(reverse=True)
        registros = []
        for nombre in archivos:
            with open(f"{self.sd_logger.mount_point}/{nombre}", 'r') as f:
                lineas = f.readlines()[1:]
                registros = lineas[-cantidad:] + registros
                if len(registros) >= cantidad:
                    break
        return registros[-cantidad:]

    async def _send(self, conn, message):
        """
        Envía un mensaje codificado en WebSocket al cliente.

        Args:
            conn (socket): Conexión activa del cliente.
            message (str): Mensaje en formato JSON.
        """
        payload = message.encode()
        header = bytearray([0x81])
        l = len(payload)
        if l < 126:
            header.append(l)
        elif l < (1 << 16):
            header.extend([126]); header.extend(l.to_bytes(2,'big'))
        else:
            header.extend([127]); header.extend(l.to_bytes(8,'big'))
        try:
            conn.send(header + payload)
        except:
            conn.close(); self.connections.pop(conn, None)

    def update_flags(self, sd_montada):
        """
        Actualiza los indicadores de estado del servidor.

        Args:
            sd_montada (bool): Indica si la tarjeta SD está montada.
        """
        self.flags['guardando'] = sd_montada
