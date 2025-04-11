import asyncio
import random
import os
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
import json
import websockets  

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

screen_height = Window.height
screen_width = Window.width

fuente_grande = int(screen_height * 0.05)
fuente_media = int(screen_height * 0.035)
fuente_chica = int(screen_height * 0.03)

class Fondo(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.dibujar_degradado, pos=self.dibujar_degradado)
        self.color1 = (1, 1, 1)
        self.color2 = (0.5, 0.5, 0.5)

    def dibujar_degradado(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            for i in range(100):
                r = self.color1[0] + (self.color2[0] - self.color1[0]) * (i / 100)
                g = self.color1[1] + (self.color2[1] - self.color1[1]) * (i / 100)
                b = self.color1[2] + (self.color2[2] - self.color1[2]) * (i / 100)
                Color(r, g, b, 1)
                Rectangle(pos=(self.x, self.y + (self.height * i / 100)), size=(self.width, self.height / 100))

    def cambiar_colores(self, color1, color2):
        self.color1 = self.hex_a_rgb(color1)
        self.color2 = self.hex_a_rgb(color2)
        self.dibujar_degradado()

    def hex_a_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


class ClimaApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.activo = True
        self.tasks = [] 

    async def async_run(self, **kwargs):
        task = asyncio.create_task(self.iniciar_websocket())
        self.tasks.append(task)
        await super().async_run(**kwargs)
        
    def build(self):
        self.condicion_actual = "normal_dia"
        self.ruta_imagenes = "img/"
        LabelBase.register(name="PixelifySans", fn_regular="fonts/PixelifySans.ttf")
        self.fondo = Fondo(size_hint=(1, 1))
        root = FloatLayout(size_hint=(1, 1))
        self.contenedor = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

        self.imagen_label = Image(size_hint=(1, 0.4))
        self.label_condicion = Label(text="--", font_name="PixelifySans", font_size=fuente_grande, bold=True, size_hint=(1, None), height=screen_height * 0.08)
        self.label_temp = Label(text="Temperatura: -- °C", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.label_hum = Label(text="Humedad: -- %", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.label_pres = Label(text="Presión: -- hPa", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)

        self.btn_actualizar = Button(text="Actualizar Clima", font_name="PixelifySans", font_size=fuente_chica, size_hint=(1, 0.08))
        self.btn_ver_todas = Button(text="Ver todas las condiciones", font_name="PixelifySans", font_size=fuente_chica, size_hint=(1, 0.08))

        self.contenedor.add_widget(self.imagen_label)
        self.contenedor.add_widget(self.label_condicion)
        self.contenedor.add_widget(self.label_temp)
        self.contenedor.add_widget(self.label_hum)
        self.contenedor.add_widget(self.label_pres)
        self.contenedor.add_widget(self.btn_actualizar)
        self.contenedor.add_widget(self.btn_ver_todas)

        root.add_widget(self.fondo)
        root.add_widget(self.contenedor)

        self.btn_actualizar.bind(on_press=self.simular_actualizacion)
        self.btn_ver_todas.bind(on_press=self.ver_todas_las_condiciones)

        self.actualizar_fondo()
        return root

    async def iniciar_websocket(self):
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
                            Clock.schedule_once(lambda dt: self.actualizar_clima(temperatura, humedad, presion, condicion))
                        except Exception as e:
                            print(f"❌ Error procesando datos: {e}")
            except Exception as e:
                if self.activo:
                    print(f"🔁 Reintentando conexión WebSocket en 5s: {e}")
                    await asyncio.sleep(5)
        
    def on_stop(self):
        print("🛑 Aplicación cerrada por el usuario")
        self.activo = False  
        for task in self.tasks:
            task.cancel()


    def actualizar_clima(self, temperatura, humedad, presion, condicion=None):
        self.condicion_actual = condicion
        self.label_temp.text = f"Temperatura: {temperatura} °C"
        self.label_hum.text = f"Humedad: {humedad} %"
        self.label_pres.text = f"Presión: {presion} hPa"
        self.label_condicion.text = self.condicion_actual
        self.cargar_imagen(self.condicion_actual)
        self.actualizar_fondo()

    def cargar_imagen(self, condicion):
        imagen_path = os.path.join(self.ruta_imagenes, f"{condicion}.png")
        if os.path.exists(imagen_path):
            self.imagen_label.source = imagen_path
        else:
            print(f"Imagen no encontrada: {imagen_path}")

    def actualizar_fondo(self):
        color_top, color_bottom = colores.get(self.condicion_actual, ("", ""))
        self.fondo.cambiar_colores(color_top, color_bottom)

    def simular_actualizacion(self, instance):
        temperatura = round(random.uniform(-5, 40), 1)
        humedad = random.randint(20, 100)
        presion = random.randint(950, 1050)
        self.actualizar_clima(temperatura, humedad, presion)

    def ver_todas_las_condiciones(self, instance):
        condiciones = list(colores.keys())
        self.mostrar_siguiente_condicion(condiciones, 0)

    def mostrar_siguiente_condicion(self, condiciones, index):
        if index < len(condiciones):
            self.condicion_actual = condiciones[index]
            self.label_condicion.text = self.condicion_actual
            self.cargar_imagen(self.condicion_actual)
            self.actualizar_fondo()
            Clock.schedule_once(lambda dt: self.mostrar_siguiente_condicion(condiciones, index + 1), 2)
        else:
            self.mostrar_siguiente_condicion(condiciones, 0)

if __name__ == '__main__':
    import sys
    try:
        asyncio.run(ClimaApp().async_run(async_lib='asyncio'))
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)
