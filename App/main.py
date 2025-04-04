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
from kivy.config import Config
import time
from kivy.uix.floatlayout import FloatLayout  # Importamos FloatLayout
from kivy.clock import Clock

# Configuración de la ventana
Config.set('graphics', 'width', '600')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'resizable', False)

# Diccionario de colores para cada condición climática
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
    def build(self):
        self.condicion_actual = "normal_dia"
       self.ruta_imagenes = r"img/"

        # Registrar fuente personalizada
        LabelBase.register(name="PixelifySans", fn_regular=r"fonts/PixelifySans.ttf")

        # Crear el fondo con degradado
        self.fondo = Fondo(size_hint=(1, 1))  # Esto asegura que ocupe todo el espacio

        # Layout principal usando FloatLayout para que el fondo no colisione con los demás elementos
        root = FloatLayout(size_hint=(1, 1))

        # Contenedor de contenido (con imagen, etiquetas y botones)
        self.contenedor = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

        # Crear widgets
        self.imagen_label = Image(size_hint=(1, 0.5))  # Imagen más grande
        self.label_condicion = Label(text="--", font_name="PixelifySans", font_size=40, bold=True, size_hint=(1, None), height=50)
        self.label_temp = Label(text="Temperatura: -- °C", font_name="PixelifySans", font_size=28, size_hint=(1, None), height=40)
        self.label_hum = Label(text="Humedad: -- %", font_name="PixelifySans", font_size=28, size_hint=(1, None), height=40)
        self.label_pres = Label(text="Presión: -- hPa", font_name="PixelifySans", font_size=28, size_hint=(1, None), height=40)

        # Botones
        self.btn_actualizar = Button(text="Actualizar Clima", font_name="PixelifySans", font_size=24, size_hint=(1, 0.1))
        self.btn_ver_todas = Button(text="Ver todas las condiciones", font_name="PixelifySans", font_size=24, size_hint=(1, 0.1))

        # Agregar widgets al contenedor
        self.contenedor.add_widget(self.imagen_label)
        self.contenedor.add_widget(self.label_condicion)
        self.contenedor.add_widget(self.label_temp)
        self.contenedor.add_widget(self.label_hum)
        self.contenedor.add_widget(self.label_pres)
        self.contenedor.add_widget(self.btn_actualizar)
        self.contenedor.add_widget(self.btn_ver_todas)

        # Agregar contenedor al root
        root.add_widget(self.fondo)  # Fondo al fondo, no ocupa espacio
        root.add_widget(self.contenedor)  # Los widgets se apilan sobre el fondo

        # Conectar eventos
        self.btn_actualizar.bind(on_press=self.simular_actualizacion)
        self.btn_ver_todas.bind(on_press=self.ver_todas_las_condiciones)

        # Aplicar fondo inicial
        self.actualizar_fondo()

        return root

    def actualizar_clima(self, temperatura, humedad, presion):
        self.condicion_actual = determinar_condiciones_climaticas(temperatura, humedad, presion)
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
            # Volver al inicio cuando se lleguen todas las condiciones
            self.mostrar_siguiente_condicion(condiciones, 0)

def determinar_condiciones_climaticas(temperatura, humedad, presion):
    # Determinar la condición climática basada en los parámetros
    hora = time.localtime().tm_hour
    if presion < 1000 and humedad > 80:
        return "lluvia"
    elif 1000 <= presion <= 1010 and humedad > 70:
        return "nublado"
    elif presion > 1015 and humedad < 60:
        return "despejado"
    elif temperatura > 35 and humedad < 40:
        return "calor"
    elif temperatura < 0 and presion > 1020:
        return "frio"
    elif presion < 995 and humedad < 50:
        return "viento"
    elif hora >= 18 or hora < 6:  # Si es de noche
        return "normal_noche"
    else:
        return "normal_dia"

if __name__ == '__main__':
    ClimaApp().run()
