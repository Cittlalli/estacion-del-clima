# Importación de módulos necesarios
import asyncio
import random
import os
import json
import websockets  

# Módulos de Kivy para interfaz gráfica
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock

# Diccionario de colores para diferentes condiciones climáticas
colores = {
    "tormenta": ("#1f1d59", "#3264a8"),
    "nublado": ("#515159", "#8f8f8f"),
    "lluvia": ("#455875", "#627696"),
    "despejado": ("#4373bf", "#6991d1"),
    "calor": ("#9e5531", "#c7aa2a"),
    "frio": ("#5b7d8a", "#7ab9de"),
    "normal_dia": ("#B0C4DE", "#5A9BD5"),
    "normal_noche": ("#4B0082", "#2F4F4F"),
    "viento": ("#8395a7", "#a0a0a0")
}

# Obtener dimensiones de la ventana para cálculo de tamaños de fuente
screen_height = Window.height
screen_width = Window.width

# Tamaños de fuente relativos al alto de pantalla
fuente_grande = int(screen_height * 0.05)
fuente_media = int(screen_height * 0.035)
fuente_chica = int(screen_height * 0.03)

# Clase para dibujar el fondo con degradado dinámico
class Fondo(Widget):
    """
    Widget personalizado que dibuja un fondo con un degradado vertical dinámico
    entre dos colores. Se puede actualizar en tiempo real con nuevos colores
    mediante la función `cambiar_colores`.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.dibujar_degradado, pos=self.dibujar_degradado)
        self.color1 = (1, 1, 1)
        self.color2 = (0.5, 0.5, 0.5)

    # Dibuja un degradado vertical entre color1 y color2
    def dibujar_degradado(self, *args):
        """
        Redibuja el degradado de fondo cuando cambian el tamaño o la posición del widget.
        Crea un degradado lineal entre color1 y color2.
        """
        self.canvas.before.clear()
        with self.canvas.before:
            for i in range(100):
                r = self.color1[0] + (self.color2[0] - self.color1[0]) * (i / 100)
                g = self.color1[1] + (self.color2[1] - self.color1[1]) * (i / 100)
                b = self.color1[2] + (self.color2[2] - self.color1[2]) * (i / 100)
                Color(r, g, b, 1)
                Rectangle(pos=(self.x, self.y + (self.height * i / 100)), size=(self.width, self.height / 100))

    # Cambia los colores del degradado
    def cambiar_colores(self, color1, color2):
        """
        Cambia los colores del degradado y lo redibuja.

        Args:
            color1 (str): Color hexadecimal inicial del degradado.
            color2 (str): Color hexadecimal final del degradado.
        """
        self.color1 = self.hex_a_rgb(color1)
        self.color2 = self.hex_a_rgb(color2)
        self.dibujar_degradado()

    # Convierte un color en formato hexadecimal a RGB normalizado
    def hex_a_rgb(self, hex_color):
        """
        Convierte un color hexadecimal a una tupla RGB con valores normalizados (0 a 1).

        Args:
            hex_color (str): Color en formato hexadecimal (ej. "#FF00FF").

        Returns:
            tuple: Color en formato (r, g, b).
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

# Clase principal de la aplicación
class ClimaApp(App):
    """
    Clase principal de la aplicación Kivy que muestra información climática
    obtenida a través de WebSockets y actualiza la interfaz gráfica con condiciones
    visuales como imágenes y colores de fondo.
    """
    def __init__(self, **kwargs):
        """
        Inicializa la aplicación, estableciendo banderas de control y tareas asíncronas.
        """
        super().__init__(**kwargs)
        self.activo = True  # Bandera para mantener la app corriendo
        self.tasks = []     # Lista de tareas asíncronas

    # Método de ejecución principal con integración de asyncio
    async def async_run(self, **kwargs):
        """
        Ejecuta la aplicación de forma asíncrona y lanza la tarea del WebSocket.
        """
        task = asyncio.create_task(self.iniciar_websocket())
        self.tasks.append(task)
        await super().async_run(**kwargs)
        
    # Crea y retorna el layout principal de la app
    def build(self):
        """
        Construye y devuelve la interfaz gráfica de la aplicación.

        Returns:
            Widget: El layout raíz que contiene todos los elementos de la UI.
        """
        self.condicion_actual = "normal_dia"
        self.ruta_imagenes = "img/"
        LabelBase.register(name="PixelifySans", fn_regular="fonts/PixelifySans.ttf")
        self.fondo = Fondo(size_hint=(1, 1))
        root = FloatLayout(size_hint=(1, 1))
        self.contenedor = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

        # Elementos visuales de la interfaz
        self.imagen_label = Image(size_hint=(1, 0.4))
        self.label_condicion = Label(text="--", font_name="PixelifySans", font_size=fuente_grande, bold=True, size_hint=(1, None), height=screen_height * 0.08)
        self.label_temp = Label(text="Temperatura: -- °C", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.label_hum = Label(text="Humedad: -- %", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.label_pres = Label(text="Presión: -- hPa", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)

        # Botones
        self.btn_actualizar = Button(text="Actualizar Clima", font_name="PixelifySans", font_size=fuente_chica, size_hint=(1, 0.08))
        self.btn_ver_todas = Button(text="Ver todas las condiciones", font_name="PixelifySans", font_size=fuente_chica, size_hint=(1, 0.08))

        # Agregar widgets al contenedor
        self.contenedor.add_widget(self.imagen_label)
        self.contenedor.add_widget(self.label_condicion)
        self.contenedor.add_widget(self.label_temp)
        self.contenedor.add_widget(self.label_hum)
        self.contenedor.add_widget(self.label_pres)
        self.contenedor.add_widget(self.btn_actualizar)
        self.contenedor.add_widget(self.btn_ver_todas)

        # Agregar fondo y contenedor al layout raíz
        root.add_widget(self.fondo)
        root.add_widget(self.contenedor)

        # Conectar eventos de botones
        self.btn_actualizar.bind(on_press=self.simular_actualizacion)
        self.btn_ver_todas.bind(on_press=self.ver_todas_las_condiciones)

        # Inicializa fondo con colores por defecto
        self.actualizar_fondo()
        return root

    # Inicia la conexión WebSocket y escucha mensajes continuamente
    async def iniciar_websocket(self):
        """
        Se conecta de forma persistente a un servidor WebSocket, escucha mensajes entrantes
        y actualiza la interfaz cuando recibe nuevos datos.
        """
        uri = "ws://192.168.0.106:8765"
        while self.activo:
            try:
                async with websockets.connect(uri) as websocket:
                    print("✅ Conectado al WebSocket")
                    while self.activo:
                        message = await websocket.recv()
                        print(f"📡 Mensaje recibido: {message}")
                        try:
                            datos = json.loads(message)
                            temperatura = datos.get("temperatura", 0)
                            humedad = datos.get("humedad", 0)
                            presion = datos.get("presion", 0)
                            condicion = datos.get("condicion", "normal_dia")
                            # Actualizar UI desde hilo principal
                            Clock.schedule_once(lambda dt: self.actualizar_clima(temperatura, humedad, presion, condicion))
                        except Exception as e:
                            print(f"❌ Error procesando datos: {e}")
            except Exception as e:
                if self.activo:
                    print(f"🔁 Reintentando conexión WebSocket en 5s: {e}")
                    await asyncio.sleep(5)
    
    # Llamado al cerrar la aplicación
    def on_stop(self):
        """
        Evento que se dispara cuando la aplicación se cierra.
        Cancela tareas y cierra la conexión de forma segura.
        """
        print("🛑 Aplicación cerrada por el usuario")
        self.activo = False  
        for task in self.tasks:
            task.cancel()

    # Actualiza las etiquetas de clima e imagen de fondo
    def actualizar_clima(self, temperatura, humedad, presion, condicion=None):
        """
        Actualiza las etiquetas, imagen y colores de fondo de la aplicación según los datos recibidos.

        Args:
            temperatura (float): Temperatura en grados Celsius.
            humedad (int): Humedad relativa en porcentaje.
            presion (int): Presión atmosférica en hPa.
            condicion (str, optional): Condición climática (clave del diccionario `colores`).
        """
        self.condicion_actual = condicion
        self.label_temp.text = f"Temperatura: {temperatura} °C"
        self.label_hum.text = f"Humedad: {humedad} %"
        self.label_pres.text = f"Presión: {presion} hPa"
        self.label_condicion.text = self.condicion_actual
        self.cargar_imagen(self.condicion_actual)
        self.actualizar_fondo()

    # Carga la imagen de acuerdo con la condición climática
    def cargar_imagen(self, condicion):
        """
        Carga y muestra la imagen correspondiente a la condición climática dada.

        Args:
            condicion (str): Nombre de la condición climática (ej. "lluvia", "frio").
        """
        imagen_path = os.path.join(self.ruta_imagenes, f"{condicion}.png")
        if os.path.exists(imagen_path):
            self.imagen_label.source = imagen_path
        else:
            print(f"Imagen no encontrada: {imagen_path}")

    # Cambia el degradado del fondo según condición
    def actualizar_fondo(self):
        """
        Cambia los colores del fondo según la condición climática actual.
        """
        color_top, color_bottom = colores.get(self.condicion_actual, ("", ""))
        self.fondo.cambiar_colores(color_top, color_bottom)

    # Simula una actualización aleatoria del clima
    def simular_actualizacion(self, instance):
        """
        Simula una actualización aleatoria del clima cuando se presiona el botón
        'Actualizar Clima'. Útil para pruebas sin conexión a WebSocket.
        """
        temperatura = round(random.uniform(-5, 40), 1)
        humedad = random.randint(20, 100)
        presion = random.randint(950, 1050)
        self.actualizar_clima(temperatura, humedad, presion)

    # Cicla por todas las condiciones disponibles visualmente
    def ver_todas_las_condiciones(self, instance):
        """
        Muestra todas las condiciones climáticas disponibles en secuencia, cambiando
        automáticamente cada 2 segundos.
        """
        condiciones = list(colores.keys())
        self.mostrar_siguiente_condicion(condiciones, 0)

    # Muestra cada condición una por una cada 2 segundos
    def mostrar_siguiente_condicion(self, condiciones, index):
        """
        Muestra una condición climática por vez, en orden secuencial.

        Args:
            condiciones (list): Lista de nombres de condiciones climáticas.
            index (int): Índice actual de la condición a mostrar.
        """
        if index < len(condiciones):
            self.condicion_actual = condiciones[index]
            self.label_condicion.text = self.condicion_actual
            self.cargar_imagen(self.condicion_actual)
            self.actualizar_fondo()
            Clock.schedule_once(lambda dt: self.mostrar_siguiente_condicion(condiciones, index + 1), 2)
        else:
            self.mostrar_siguiente_condicion(condiciones, 0)

# Punto de entrada principal
if __name__ == '__main__':
    import sys
    try:
        asyncio.run(ClimaApp().async_run(async_lib='asyncio'))
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)
