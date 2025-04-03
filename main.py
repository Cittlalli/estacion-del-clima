import sys
import os
import random
from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QBrush, QFontDatabase
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton

def punto_de_rocio(temperatura, humedad):
    return temperatura - ((100 - humedad) / 5)

def determinar_condiciones_climaticas(temperatura, humedad, presion):
    if presion < 1000 and humedad > 80:
        return "lluvia"
    elif 1000 <= presion <= 1010 and humedad > 70:
        return "nublado"
    elif presion > 1015 and humedad < 60:
        return "despejado"
    elif humedad > 90 and (temperatura - punto_de_rocio(temperatura, humedad)) < 2:
        return "nublado"
    elif temperatura > 35 and humedad < 40:
        return "calor"
    elif temperatura < 0 and presion > 1020:
        return "frio"
    elif presion < 995 and humedad > 85 and temperatura > 20:
        return "tormenta"
    elif presion < 980 and humedad > 85:
        return "viento"
    elif temperatura < 3 and presion > 1015 and humedad < 60:
        return "frio"
    elif presion > 1010 and humedad < 50:
        return "viento"
    else:
        hora_actual = QTime.currentTime().hour()
        return "normal_dia" if 6 <= hora_actual < 18 else "normal_noche"

# Configuracion App
class ClimaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.condicion_actual = "normal_dia"  # Valor inicial

        # Ruta imagenes
        self.ruta_imagenes = r"C:\\Users\\metis_17gpyox\\Desktop\\Proyecto Estacion del Clima\\imagenes"
        self.setWindowTitle("Aplicación del Clima")
        self.setGeometry(100, 100, 600, 600)
        self.setMinimumSize(300, 400)  # Tamaño mínimo para celulares
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)


        # Ruta fuente
        font_db = QFontDatabase()
        font_id = font_db.addApplicationFont(r"C:\Users\metis_17gpyox\Desktop\Proyecto Estacion del Clima\fuentes\PixelifySans.ttf")
        font_family = font_db.applicationFontFamilies(font_id)[0]
        font = QFont(font_family, 20)

        # Configuracion layout
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)

        self.label_layout = QVBoxLayout()
        self.label_layout.setAlignment(Qt.AlignCenter)

        self.imagen_label = QLabel(self)
        self.imagen_label.setAlignment(Qt.AlignCenter)
        
        # Configuracion etiquetas
        self.label_temp = QLabel("Temperatura: -- °C")
        self.label_hum = QLabel("Humedad: -- %")
        self.label_pres = QLabel("Presión: -- hPa")
        self.label_condicion = QLabel("--")

        self.label_temp.setFont(font)
        self.label_hum.setFont(font)
        self.label_pres.setFont(font)
        self.label_condicion.setFont(font)

        self.label_temp.setStyleSheet("color: white; text-align: center;")
        self.label_hum.setStyleSheet("color: white; text-align: center;")
        self.label_pres.setStyleSheet("color: white; text-align: center;")
        self.label_condicion.setStyleSheet("color: white; text-align: center;")

        self.label_temp.setAlignment(Qt.AlignCenter)
        self.label_hum.setAlignment(Qt.AlignCenter)
        self.label_pres.setAlignment(Qt.AlignCenter)
        self.label_condicion.setAlignment(Qt.AlignCenter)

        self.label_layout.addWidget(self.label_temp)
        self.label_layout.addWidget(self.label_hum)
        self.label_layout.addWidget(self.label_pres)
        self.label_layout.addWidget(self.label_condicion)

        # Configuracion boton
        self.btn_actualizar = QPushButton("Actualizar Clima")
        self.btn_actualizar.setFont(font)
        self.btn_actualizar.setStyleSheet("text-align: center;")
        self.btn_actualizar.clicked.connect(self.simular_actualizacion)
        
        self.btn_ver_todas = QPushButton("Ver todas las condiciones")
        self.btn_ver_todas.setFont(font)
        self.btn_ver_todas.setStyleSheet("text-align: center;")
        self.btn_ver_todas.clicked.connect(self.ver_todas_las_condiciones)

        self.btn_actualizar.setSizePolicy(self.btn_actualizar.sizePolicy().Expanding, self.btn_actualizar.sizePolicy().Preferred)
        self.btn_ver_todas.setSizePolicy(self.btn_ver_todas.sizePolicy().Expanding, self.btn_ver_todas.sizePolicy().Preferred)

        # Añadir elementos al layout principal

        self.layout.addWidget(self.imagen_label, alignment=Qt.AlignCenter)
        self.layout.addLayout(self.label_layout)
        self.layout.addWidget(self.btn_actualizar, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.btn_ver_todas, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        
        condition = self.label_condicion.text().replace("","")
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
        
        color_top, color_bottom = colores.get(self.condicion_actual.lower(), ("#87CEFA", "#FFFFFF"))
        
        gradient.setColorAt(0, QColor(color_top))
        gradient.setColorAt(1, QColor(color_bottom))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, 0, self.width(), self.height())
    
    def actualizar_clima(self, temperatura, humedad, presion):
        self.condicion_actual = determinar_condiciones_climaticas(temperatura, humedad, presion)
        self.label_temp.setText(f"Temperatura: {temperatura} °C")
        self.label_hum.setText(f"Humedad: {humedad} %")
        self.label_pres.setText(f"Presión: {presion} hPa")
        self.label_condicion.setText(f"{self.condicion_actual}")
        self.cargar_imagen(self.condicion_actual)
        self.repaint()
    
    def cargar_imagen(self, condicion):
        imagen_path = os.path.join(self.ruta_imagenes, f"{condicion}.png")
        pixmap = QPixmap(imagen_path)
        
        if pixmap.isNull():
            print(f"Error al cargar la imagen: {imagen_path}")
        else:
            self.imagen_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def ver_todas_las_condiciones(self):
        condiciones = ["tormenta", "nublado", "lluvia", "despejado", "calor", "frio", "normal_dia", "normal_noche", "viento"]
        self.mostrar_siguiente_condicion(condiciones, 0)
    
    def mostrar_siguiente_condicion(self, condiciones, index):
        if index < len(condiciones):
            self.condicion_actual = condiciones[index]
            self.label_condicion.setText(self.condicion_actual)
            self.cargar_imagen(self.condicion_actual)
            self.repaint()
            QTimer.singleShot(1000, lambda: self.mostrar_siguiente_condicion(condiciones, index + 1))
    
    def simular_actualizacion(self):
        temperatura = round(random.uniform(-5, 40), 1)
        humedad = random.randint(20, 100)
        presion = random.randint(950, 1050)
        self.actualizar_clima(temperatura, humedad, presion)

    def resizeEvent(self, event):
        nuevo_ancho = self.width()
        nuevo_alto = self.height()

        # Verifica si hay una imagen antes de redimensionarla
        if self.imagen_label.pixmap():
            self.imagen_label.setPixmap(self.imagen_label.pixmap().scaled(
                nuevo_ancho // 2, nuevo_alto // 3, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

        # Ajusta tamaño de la fuente
        nuevo_tamano_fuente = max(10, nuevo_ancho // 30)
        self.label_temp.setFont(QFont(self.label_temp.font().family(), nuevo_tamano_fuente))
        self.label_hum.setFont(QFont(self.label_hum.font().family(), nuevo_tamano_fuente))
        self.label_pres.setFont(QFont(self.label_pres.font().family(), nuevo_tamano_fuente))
        self.label_condicion.setFont(QFont(self.label_condicion.font().family(), nuevo_tamano_fuente))

        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClimaApp()
    window.show()
    sys.exit(app.exec_())
