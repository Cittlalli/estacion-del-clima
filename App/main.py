"""
Este módulo implementa una aplicación gráfica interactiva usando Kivy, que visualiza en tiempo real
datos meteorológicos obtenidos vía WebSocket. Además, permite mostrar un historial de datos mediante gráficos.

Funcionalidades principales:
- Conexión asíncrona a un servidor WebSocket.
- Visualización de temperatura, humedad, presión y condiciones climáticas.
- Cambio dinámico de fondo y gráficos en función del clima.
- Navegación entre la vista principal y una pantalla de gráficos históricos.

Requiere:
- Kivy
- websockets
- matplotlib
- asyncio
- Kivy Garden (matplotlib backend)
"""

# Importación de módulos necesarios
import asyncio
import random
import os
import json
import websockets 
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.animation import FuncAnimation

# Módulos de Kivy para interfaz gráfica
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

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

# Carga de la fuente de la aplicación 
LabelBase.register(name="PixelifySans", fn_regular="fonts/PixelifySans.ttf")
ruta_fuente = "fonts/PixelifySans.ttf"
try:
    PROP_PIX = FontProperties(fname=ruta_fuente)
except Exception as e:
    print(f"[ERROR] No se pudo cargar la fuente: {e}")
    PROP_PIX = None

class WebSocketClient:
    """
    Cliente WebSocket que gestiona la conexión con el servidor de clima y comunica
    los datos recibidos a la interfaz gráfica en Kivy.

    Atributos:
        activo (bool): Controla si la conexión WebSocket está activa.
        uri (str): Dirección del servidor WebSocket.
        websocket (websockets.WebSocketClientProtocol): Instancia de la conexión actual.
        send_queue (asyncio.Queue): Cola de mensajes pendientes por enviar.
        on_connect (Callable): Callback que se ejecuta al conectarse.
        on_historial_recibido (Callable): Callback que se llama al recibir datos históricos.

    Métodos principales:
        iniciar_websocket(): Inicia y mantiene la conexión WebSocket.
        enviar_mensaje(mensaje): Encola un mensaje para ser enviado.
        cambiar_tipo(tipo): Cambia el modo de recepción (real/historial).
        on_message(mensaje): Procesa los mensajes recibidos del servidor.
        on_stop(): Detiene la conexión de manera segura.
    """

    def __init__(self):
        self.activo = True
        self.callback_historial = None
        self.uri ="ws://192.168.0.105:8765"#"ws://192.168.1.80:8765"
        self.tasks = []
        self.tipo = "real"

        self.websocket = None 
        self.on_connect = None
        self.on_historial_recibido = None  # Callback
        self.send_queue = asyncio.Queue()

    async def iniciar_websocket(self):
        """
        Se conecta de forma persistente a un servidor WebSocket, escucha mensajes entrantes
        y actualiza la interfaz cuando recibe nuevos datos.
        """
        while self.activo:
            try:
                async with websockets.connect(self.uri, ping_interval=None, compression=None) as websocket:
                    self.websocket = websocket
                    print("✅ Conectado al WebSocket")
                    if self.on_connect:
                        Clock.schedule_once(lambda dt: self.on_connect())
                        send_task = asyncio.create_task(self._send_loop())
                        self.tasks.append(send_task)
                    while self.activo:
                        message = await websocket.recv()
                        print(f"📡 Mensaje recibido: {message}")
                        try:
                            self.on_message(message)       
                        except Exception as e:
                            print(f"❌ Error procesando datos: {e}")
                    send_task.cancel()
                    self.websocket = None
            except Exception as e:
                if self.activo:
                    print(f"🔁 Reintentando conexión WebSocket en 5s: {e}")
                    await asyncio.sleep(5)

    def on_stop(self):
        """
        Evento que se dispara cuando la aplicación se cierra.
        Cancela tareas y cierra la conexión de forma segura.
        """
        print("🛑 Aplicación cerrada por el usuario")
        self.activo = False
        for task in self.tasks:
            task.cancel()

    def cambiar_tipo(self, tipo):
        """
        Cambia el tipo de conexion del cliente y los datos que recibirá
        """
        self.tipo = tipo
        if tipo == "real":
            self.enviar_mensaje(json.dumps({"solicitud": "real"}))
        elif tipo == "historial":
            self.enviar_mensaje(json.dumps({"solicitud": "historial"}))

    def on_message(self, mensaje):
        """
        Lee los datos enviados desde el servidor
        """
        try:
            datos = json.loads(mensaje)
            tipo = self.tipo

            if tipo == "real":
                temperatura = datos.get("temperatura", 0)
                humedad = datos.get("humedad", 0)
                presion = datos.get("presion", 0)
                condicion = datos.get("condicion", "normal_dia")
                enviando = datos.get("enviando", False)
                conectado = datos.get("conectado", False)
                guardando = datos.get("guardando", False)
                # Actualizar UI desde hilo principal
                Clock.schedule_once(lambda dt: self.actualizar_clima(temperatura, humedad, presion, condicion))
                Clock.schedule_once(lambda dt: self.actualizar_estado(conectado, enviando, guardando))             
            elif tipo == "historial":
                historial = []
                for linea in datos["historial"]:
                    try:
                        historial.append({
                            "hora":         linea["hora"],
                            "temperatura":  float(linea["temperatura"]),
                            "presion":      float(linea["presion"]),
                            "humedad":      float(linea["humedad"]),
                        })
                    except Exception as e:
                        print(f"❌ Error procesando entrada: {datos} -> {e}")
                Clock.schedule_once(lambda dt: self.on_historial_recibido(historial))
        except Exception as e:
            print("Error al procesar mensaje:", e)

    def enviar_mensaje(self, mensaje):
        """
        Agrega un mensaje a la lista
        """
        envmsg_task = asyncio.create_task(self._enviar_mensaje(mensaje))
        self.tasks.append(envmsg_task)

    async def _enviar_mensaje(self, mensaje):
        """
        Método privado que envía un mensaje a través de WebSocket de manera asíncrona.
        """
        try:
            if self.websocket:
                await self.websocket.send(mensaje)
                print(f"📤 Mensaje enviado: {mensaje}")
            else:
                print("⚠️ No hay conexión WebSocket activa para enviar mensajes.")
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
    
    async def _send_loop(self):
        """
        Saca mensajes de la lista y los envía sólo si la conexión está activa.
        """
        while True:
            msg = await self.send_queue.get()
            if self.websocket and not self.websocket.closed:
                try:
                    await self.websocket.send(msg)
                    print(f"📤 Mensaje enviado: {msg}")
                except Exception as e:
                    print(f"❌ Error enviando mensaje: {e}")
            else:
                print("⚠️ No hay conexión WebSocket activa para enviar mensajes.")

# Clase para dibujar el fondo con degradado dinámico
class Fondo(Widget):
    """
    Widget personalizado para dibujar un fondo degradado verticalmente,
    útil para indicar visualmente diferentes condiciones climáticas.

    Métodos:
        dibujar_degradado(): Redibuja el degradado al cambiar tamaño o posición.
        cambiar_colores(color1, color2): Cambia los colores de inicio y fin del degradado.
        hex_a_rgb(hex_color): Convierte un color hexadecimal a RGB normalizado.
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

class MainScreen(Screen):
    """
    Pantalla principal de la aplicación donde se muestran los datos climáticos actuales.

    Atributos:
        app: Instancia de la aplicación principal.
        fondo (Fondo): Widget de fondo con degradado.
        contenedor (BoxLayout): Contenedor principal de widgets.

    Métodos:
        actualizar_clima(temperatura, humedad, presion, condicion): Actualiza etiquetas y fondo.
        actualizar_fondo(): Cambia el fondo según la condición actual.
        cargar_imagen(condicion): Carga la imagen correspondiente a la condición.
        actualizar_estado(wifi_on, enviando, sd_on): Actualiza la barra de estado superior.
        habilitar_historial(): Activa el botón de historial una vez conectado.
    """
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.name = "main"   

        self.app.condicion_actual = "normal_dia"
        self.app.ruta_imagenes = "img/"
        
        self.app.fondo = Fondo(size_hint=(1, 1))
        root = FloatLayout(size_hint=(1, 1))
        self.app.contenedor = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

        # Estados
        self.app.label_estado = Label(
            text="WiFi: --  |  Enviando: --  |  SD: --",
            font_name="PixelifySans",
            font_size=fuente_chica,
            size_hint=(1, None),
            height=screen_height * 0.04
        )
        self.app.contenedor.add_widget(self.app.label_estado)

        # Elementos visuales de la interfaz
        self.app.imagen_label = Image(size_hint=(1, 0.4))
        self.app.label_condicion = Label(text="--", font_name="PixelifySans", font_size=fuente_grande, bold=True, size_hint=(1, None), height=screen_height * 0.08)
        self.app.label_temp = Label(text="Temperatura: -- °C", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.app.label_hum = Label(text="Humedad: -- %", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)
        self.app.label_pres = Label(text="Presión: -- hPa", font_name="PixelifySans", font_size=fuente_media, size_hint=(1, None), height=screen_height * 0.06)

        # Botón para abrir pantalla de gráficos
        self.app.boton_graficos = Button(
            text="Ver historial",
            size_hint=(None, None),
            size=(150, 50),
            font_name="PixelifySans",
            font_size="16sp",
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 0.5),
            color=(1, 1, 1, 1),
        )       
        self.app.boton_graficos.disabled = True
        self.app.boton_graficos.bind(on_release=self.app.cambiar_pantalla)

        # Agregar widgets al contenedor
        self.app.contenedor.add_widget(self.app.imagen_label)
        self.app.contenedor.add_widget(self.app.label_condicion)
        self.app.contenedor.add_widget(self.app.label_temp)
        self.app.contenedor.add_widget(self.app.label_hum)
        self.app.contenedor.add_widget(self.app.label_pres)
        self.app.contenedor.add_widget(self.app.boton_graficos)

        # Agregar fondo y contenedor al layout raíz
        root.add_widget(self.app.fondo)
        root.add_widget(self.app.contenedor)
        self.add_widget(root)

        # Inicializa fondo con colores por defecto
        self.actualizar_fondo()

    def habilitar_historial(self, *args):
        """
        Callback para habilitar el botón cuando el WS conecte.
        """
        self.app.boton_graficos.disabled = False

    # Cambia el degradado del fondo según condición
    def actualizar_fondo(self):
        """
        Cambia los colores del fondo según la condición climática actual.
        """
        color_top, color_bottom = colores.get(self.app.condicion_actual, ("", ""))
        self.app.fondo.cambiar_colores(color_top, color_bottom)

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
        self.app.condicion_actual = condicion
        condicion_legible = condicion.replace('_', ' ').title() if condicion else "--"

        self.app.label_temp.text = f"Temperatura: {temperatura} °C"
        self.app.label_hum.text = f"Humedad: {humedad} %"
        self.app.label_pres.text = f"Presión: {presion} hPa"
        self.app.label_condicion.text = condicion_legible
        self.cargar_imagen(self.app.condicion_actual)
        self.actualizar_fondo()

    def actualizar_estado(self, wifi_on, enviando, sd_on):
        """
        Actualiza el texto de estado en la parte superior.
        """
        self.app.label_estado.text = f"WiFi: {'On' if wifi_on else 'Off'}  |  Enviando: {'On' if enviando else 'Off'}  |  SD: {'On' if sd_on else 'Off'}"

    # Carga la imagen de acuerdo con la condición climática
    def cargar_imagen(self, condicion):
        """
        Carga y muestra la imagen correspondiente a la condición climática dada.

        Args:
            condicion (str): Nombre de la condición climática (ej. "lluvia", "frio").
        """
        imagen_path = os.path.join(self.app.ruta_imagenes, f"{condicion}.png")
        if os.path.exists(imagen_path):
            self.app.imagen_label.source = imagen_path
        else:
            print(f"Imagen no encontrada: {imagen_path}")

class PantallaGrafica(Screen):
    """
    Pantalla secundaria que muestra gráficos de historial meteorológico (temperatura,
    humedad, presión) usando Matplotlib embebido en Kivy.

    Atributos:
        datos (list): Lista de diccionarios con información climática histórica.
        fig (Figure): Figura principal de Matplotlib.
        axes (list): Subgráficos para temperatura, humedad y presión.

    Funcionalidades:
        - Configura colores y estilos según la condición actual.
        - Crea gráficos con ejes compartidos.
        - Inserta la figura en la interfaz de Kivy.
    """
    def __init__(self, datos=None, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
       
        # Configurar fondo con degradado según condición actual
        fondo = Fondo(size_hint=(1, 1))
        cond = getattr(self.app, 'condicion_actual', 'normal_dia')
        color_top, color_bottom = colores.get(cond, ([0,0,0,1], [0,0,0,1]))
        fondo.cambiar_colores(color_top, color_bottom)

        # Colores según claridad del fondo
        cond_clara = cond in ('despejado', 'normal_dia', 'calor')
        color_linea_temp = 'red'       if cond_clara else 'orange'
        color_linea_hum  = 'blue'      if cond_clara else 'cyan'
        color_linea_pres = 'green'     if cond_clara else 'lime'
        color_texto      = 'black'     if cond_clara else 'white'

        # Layout principal
        self.root = FloatLayout(size_hint=(1, 1))
        contenedor = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=10,
            size_hint=(1, 1)
        )

        # Preparar datos
        self.datos = datos or []
        self.horas   = [d.get("hora", "") for d in self.datos]
        self.indices = list(range(len(self.horas)))
        self.y_temp  = [d.get("temperatura", 0) for d in self.datos]
        self.y_pres  = [d.get("presion", 0) for d in self.datos]
        self.y_hum   = [d.get("humedad", 0) for d in self.datos]

        # Crear figura con 3 subplots, compartiendo X
        self.fig, self.axes = plt.subplots(
            nrows=3, ncols=1,
            sharex=True,
            facecolor='none',
            figsize=(6, 8)
        )
        self.fig.patch.set_alpha(0)

        # Función para limpiar estética de cada eje
        def estilar_ax(ax):
            ax.set_facecolor('none')
            for spine in ('top', 'right'): ax.spines[spine].set_visible(False)
            ax.tick_params(axis='y', labelsize=9, colors=color_texto)
            for lbl in ax.get_yticklabels():
                lbl.set_fontproperties(PROP_PIX)

        # Configuración inicial de los gráficos
        estilar_ax(self.axes[0])
        self.axes[0].plot(self.indices, self.y_temp, linewidth=2, color=color_linea_temp)
        self.axes[0].set_title('Temperatura', fontproperties=PROP_PIX, fontsize=12, pad=6, color=color_texto)
        self.axes[0].set_ylabel('°C', fontproperties=PROP_PIX, fontsize=10, color=color_texto)

        estilar_ax(self.axes[1])
        self.axes[1].plot(self.indices, self.y_hum, linewidth=2, color=color_linea_hum)
        self.axes[1].set_title('Humedad', fontproperties=PROP_PIX, fontsize=12, pad=6, color=color_texto)
        self.axes[1].set_ylabel('%', fontproperties=PROP_PIX, fontsize=10, color=color_texto)

        estilar_ax(self.axes[2])
        self.axes[2].plot(self.indices, self.y_pres, linewidth=2, color=color_linea_pres)
        self.axes[2].set_title('Presión', fontproperties=PROP_PIX, fontsize=12, pad=6, color=color_texto)
        self.axes[2].set_ylabel('hPa', fontproperties=PROP_PIX, fontsize=10, color=color_texto)

        # X ticks
        self.axes[2].set_xticklabels(
            self.horas,
            rotation=90,
            ha='right',
            fontproperties=PROP_PIX,
            fontsize=9,
            color=color_texto
        )

        # Ajustar color de ticks del eje X
        self.axes[2].tick_params(axis='x', colors=color_texto)

        # Ajustar layout
        self.fig.tight_layout(pad=4)

        # Incrustar gráfico
        self.graf_widget = FigureCanvasKivyAgg(self.fig)
        contenedor.add_widget(self.graf_widget)

        # Botón volver transparente
        btn = Button(
            text="< Volver",
            size_hint=(1, 0.1),
            font_name="PixelifySans",
            font_size="16sp",
            background_normal='',
            background_color=(0,0,0,0),
            color=(1,1,1,1)
        )
        btn.bind(on_release=self.volver)
        contenedor.add_widget(btn)

        # Montaje final de widgets
        self.root.add_widget(fondo)
        self.root.add_widget(contenedor)
        self.add_widget(self.root)

    def volver(self, instance):
        """
            Regresa a la pantalla principal
        """
        self.app.websocket.cambiar_tipo("real")
        self.manager.current = 'main'

    def actualizar_grafica(self, nuevos_datos):
        """
            Actualiza la grafica
        """
        nuevo = nuevos_datos[-1]
        self.datos.append(nuevo)
        if len(self.datos) > 10:
            self.datos.pop(0)

        # Actualizar los datos Y
        self.horas = [d["hora"] for d in self.datos]
        self.y_temp = [d["temperatura"] for d in self.datos]
        self.y_hum = [d["humedad"] for d in self.datos]
        self.y_pres = [d["presion"] for d in self.datos]

        # Actualizar líneas directamente
        for ax in self.axes:
            ax.clear()

        self.axes[0].plot(range(len(self.y_temp)), self.y_temp, color='red')
        self.axes[1].plot(range(len(self.y_hum)), self.y_hum, color='blue')
        self.axes[2].plot(range(len(self.y_pres)), self.y_pres, color='green')

        self.axes[2].set_xticks(range(len(self.horas)))
        self.axes[2].set_xticklabels(self.horas, rotation=90)

        self.fig.tight_layout(pad=4)
        self.graf_widget.draw()

    
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
        self.activo = True  
        self.tasks = [] 
        self.websocket_client = WebSocketClient()
        
    # Método de ejecución principal con integración de asyncio
    async def async_run(self, **kwargs):
        """
        Ejecuta la aplicación de forma asíncrona y lanza la tarea del WebSocket.
        """
        task = asyncio.create_task(self.websocket_client.iniciar_websocket())
        self.tasks.append(task)
        await super().async_run(**kwargs)
        
    # Crea y retorna el layout principal de la app
    def build(self):
        self.screenmanager = ScreenManager()
        self.pantalla_principal = MainScreen(app=self)
        self.screenmanager.add_widget(self.pantalla_principal)
        
        self.websocket_client.actualizar_clima = self.pantalla_principal.actualizar_clima
        self.websocket_client.actualizar_estado = self.pantalla_principal.actualizar_estado
        self.websocket_client.on_connect = self.pantalla_principal.habilitar_historial
        self.websocket_client.on_historial_recibido = self.mostrar_grafico

        self.pantalla_principal.abrir_graficos = self.abrir_graficos

        return self.screenmanager  
    
    def mostrar_grafico(self, historial):
        """
            Muestra el grafico en la ventana
        """
        if not self.screenmanager.has_screen("grafico"):
            self.abrir_graficos(historial)
        else:
            grafico = self.screenmanager.get_screen("grafico")
            grafico.actualizar_grafica(historial)


    def cambiar_pantalla(self,instance):
        """
            Solicita el cambio de cliente
        """
        self.websocket_client.cambiar_tipo("historial")

    def abrir_graficos(self, datos):   
        """
            Abre la a la pantalla grafica
        """       
        pantalla = PantallaGrafica(datos, name="grafico")
        if not self.screenmanager.has_screen("grafico"):
            self.screenmanager.add_widget(pantalla)
        else:
            self.screenmanager.remove_widget(self.screenmanager.get_screen("grafico"))
            self.screenmanager.add_widget(pantalla)
        self.screenmanager.current = "grafico"

# Punto de entrada principal
if __name__ == '__main__':
    import sys
    try:
        asyncio.run(ClimaApp().async_run(async_lib='asyncio'))
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)
