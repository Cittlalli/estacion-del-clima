# 🌤️ Estación del Clima

Este repositorio contiene una solución completa para monitorear condiciones climáticas usando una **Raspberry Pi Pico W** y visualizar los datos desde una **aplicación móvil construida con Kivy**.  

Incluye sensores **DHT11** y **BMP280**, conectividad Wi-Fi y comunicación en tiempo real mediante WebSockets.

---

## 🗂️ Estructura del repositorio

```
Estacion-del-clima/
├── ClimaAPP.ipynb              # Notebook para compilar la APK en Google Colab
├── Raspberry/                  # Código para la Raspberry Pi Pico W (MicroPython)
│   ├── clima.py                # Lógica para determinar condiciones climáticas
│   ├── comunicacion.py         # Manejo de Wi-Fi y WebSockets
│   ├── main.py                 # Programa principal que lee sensores y envía datos
│   ├── sensors.py              # Clases para manejar los sensores DHT11 y BMP280
├── App/                        # Aplicación móvil con Kivy (Python)
│   ├── main.py                 # Interfaz gráfica y recepción de datos
│   ├── buildozer.spec          # Configuración para compilar APK
│   ├── logo.png                # Ícono de la aplicación
│   ├── fonts/                  # Tipografías utilizadas
│   └── img/                    # Imágenes de fondo según el clima
```

---

## 🧪 Ejecutar la carpeta `Raspberry` (código MicroPython) en Thonny

1. Abre **Thonny IDE**.
2. Conecta tu **Raspberry Pi Pico W** por USB.
3. Asegúrate de tener **MicroPython para RP2040** instalado.
4. Abre los archivos desde la carpeta `/Raspberry`.
5. Carga los siguientes archivos en la Pico W:
   - `main.py`
   - `sensors.py`
   - `comunicacion.py`
   - `clima.py`
6. Guarda todos en la Raspberry y reinicia la placa (o presiona `Run current script` si estás probando).
7. La Pico W se conectará al Wi-Fi, comenzará a leer los sensores y transmitirá los datos por WebSocket.

> 🔌 **Nota**: Asegúrate de configurar correctamente el SSID y la contraseña en `comunicacion.py`.

---

## 📱 Ejecutar la carpeta `App` (Kivy) en VSCode

1. Abre la carpeta `/App` en **VSCode**.
2. Instala Kivy si no lo tienes:
   ```bash
   pip install kivy
   ```
3. Corre el archivo principal:
   ```bash
   python main.py
   ```
4. Verás una interfaz gráfica que muestra:
   - Temperatura 🌡️  
   - Humedad 💧  
   - Presión atmosférica 🌬️  
   - Condición climática general con fondo animado o imagen 📷

---

## ☁️ Compilar la APK en Google Colab

1. Abre el archivo [`ClimaAPP.ipynb`](ClimaAPP.ipynb) en Google Colab.
2. Sigue los pasos del notebook para compilar la aplicación con Buildozer.
3. Sube los siguientes archivos desde la carpeta `/App` al directorio `/content` de Colab:
   - `main.py`
   - `buildozer.spec`
   - `logo.png`
   - Carpeta `fonts/`
   - Carpeta `img/`
4. Al finalizar la compilación, la **APK se guardará en**:  
   ```
   /content/bin/
   ```
5. Descarga el archivo `.apk` generado para instalarlo en tu dispositivo Android.

---

## 🚀 Características

- 📡 Comunicación en tiempo real por WebSocket
- 📈 Lectura precisa de temperatura, humedad y presión
- 🎨 UI interactiva y visual adaptable a condiciones climáticas
- 📲 Compatible con dispositivos Android
- 🧠 Lógica modular y archivos bien organizados

---

## 🛠️ Tecnologías usadas

- MicroPython (Raspberry Pi Pico W)
- Kivy (Interfaz móvil)
- WebSockets
- Google Colab + Buildozer (para compilar APK)

---
