import usocket as socket
import ujson
import time
from clima import determinar_clima
from sensores.dht_sensor import DHT11
from sensores.bmp280_sensor import BMP280

# Variables globales para almacenar las lecturas
dht_data = None   # (temperature, humidity)
bmp_data = None   # (temperature, pressure)

# Servidor Web
def web_server():
    addr = ('0.0.0.0', 80)
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Servidor Web Iniciado...")

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024)

        if dht_data is not None and bmp_data is not None:
            temp, hum = dht_data
            _, pressure = bmp_data
            condition = determinar_clima(temp, hum, pressure)

            response = ujson.dumps({
                "temperature": temp,
                "humidity": hum,
                "pressure": pressure,
                "condition": condition
            })
        else:
            response = ujson.dumps({"error": "No hay datos disponibles"})

        cl.send('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + response)
        cl.close()
        time.sleep(1)
