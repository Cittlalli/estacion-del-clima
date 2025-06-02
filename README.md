# 🌤️ Estación del Clima

Este repositorio contiene una solución completa para monitorear condiciones climáticas usando una Raspberry Pi Pico W. Visualiza los datos desde una aplicación móvil construida con Kivy y en una pantalla OLED conectada a la Raspberry Pico. Escribe y lee la informacion de una tarjeta SD.

Incluye el sensor BME280, conectividad Wi-Fi, comunicación en tiempo real mediante WebSockets, almacenamiento externo.

---

## 🗂️ Estructura del repositorio

```
Estacion-del-clima/
├── ClimaAPP.ipynb              # Notebook para compilar la APK en Google Colab
├── Bootloader.u2f              # Bootloader utilizado en la Raspberry para el proyecto
├── Raspberry/                  # Código para la Raspberry Pi Pico W (MicroPython)
│   ├── clima.py                # Lógica para determinar condiciones climáticas
│   ├── comunicacion.py         # Manejo de Wi-Fi y WebSockets
│   ├── wifi_config.json        # Redes Wi-Fi y configuración de IP estática
│   ├── main.py                 # Programa principal que lee sensores y envía datos
│   ├── sensors.py              # Clase para manejar el sensor BME280
│   ├── sd_logger.py            # Clases para manejar el modulo SD
│   ├── display.py              # Repositorio de byte arrays de estado, condiciones y
                                  logo de la empresa. Funciones de la pantalla OLED.
├── App/                        # Aplicación móvil con Kivy (Python)
│   ├── main.py                 # Interfaz gráfica y recepción de datos
│   ├── buildozer.spec          # Configuración para compilar APK
│   ├── logo.png                # Ícono de la aplicación
│   ├── fonts/                  # Tipografías utilizadas
│   └── img/                    # Imágenes según el clima
```
---

## 🪛 Pasos para instalar el bootloader:
Conecta tu Pico en modo bootloader:
1. Mantén presionado el botón BOOTSEL de tu Pico.
2. Conéctala al puerto USB de tu computadora.
3. Suelta el botón cuando aparezca una unidad nueva llamada RPI-RP2.
4. Descarga `Bootloader.u2f`
5. Arrastra el archivo a la unidad RPI-RP2.
6. La Pico se reiniciará automáticamente y dejará de aparecer como unidad USB.

Ya puedes conectarte con un editor como Thonny y empezar a cargar tus scripts MicroPython.

> ⚠️ Si usas Thonny, selecciona: Herramientas > Opciones > Intérprete y elige MicroPython (Raspberry Pi Pico) y el puerto correspondiente.

---

## 📡 Ejecutar la carpeta `Raspberry`

1. Tener MicroPython para RP2040 instalado.
2. Abrir los archivos desde la carpeta `/Raspberry`, cargarlos y guardarlos:
   - `main.py`
   - `sensors.py`
   - `comunicacion.py`
   - `clima.py`
   - `sd_logger.py`
   - `display.py`
3. Instalar las librerias `sdcard` y `ssd1306` en la Raspberry
> **Nota**: Asegúrate de configurar correctamente el SSID y la contraseña en `wifi_config.json`.

---

## 📱 Ejecutar la carpeta `App`

1. Abre VS Code Studio [En caso de no tenerlo intalado puedes hacerlo desde este link](https://code.visualstudio.com/download)
2. Abre el proyecto `main.py` de la carpeta `/App`en VS Code.
3. Abre el terminal (puedes usar Ctrl + ñ o ir a Ver > Terminal).
4. Ejecuta los siguientes comandos pip install :
   - Kivy:
     ```bash
     pip install kivy
     python -m pip install https://github.com/kivy-garden/matplotlib/archive/master.zip
     ```
   -  Kivy-Garden desde la terminal:
     ```bash
     python -m pip install https://github.com/kivy-garden/matplotlib/archive/master.zip
     ```
   - websockets
     ```bash
     pip install websockets
     ```
   - matplotlib
     ```bash
     pip install matplotlib
     ```
   > Asegúrate de que estás usando el entorno Python correcto (revisa abajo a la izquierda en VS Code el intérprete Python activo).
4. Ejecutar el archivo:
   ```bash
   python main.py
   ```
   
---

## ☁️ Compilar la APK en Google Colab

1. Descarga y abre el archivo [`ClimaAPP.ipynb`](ClimaAPP.ipynb) en [Google Colab](https://colab.research.google.com/).
2. Subir los siguientes archivos desde la carpeta `/App` al directorio `/content` de Colab:
   - `main.py`
   - `buildozer.spec`
   - `logo.png`
   - Carpeta `fonts/`
   - Carpeta `img/`
3. Realizar los pasos del notebook para compilar la aplicación con Buildozer.
4. Al finalizar la compilación, la APK se guardará en:  
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
- 🗃️ Registro de datos en memoria SD
- 📟 Visualizacion en pantalla OLED

---

## 🛠️ Tecnologías usadas

- MicroPython (Raspberry Pi Pico W)
- Kivy (Interfaz móvil)
- WebSockets
- Google Colab + Buildozer (para compilar APK)

---
