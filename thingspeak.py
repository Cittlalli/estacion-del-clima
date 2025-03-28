import urequests
import time

# Configuración de ThingSpeak
THINGSPEAK_API_KEY = "VT393EBGETRKSFK9"  # Clave API de ThingSpeak
BASE_URL = "https://api.thingspeak.com/update"

def thingspeak_send(temperature, humidity, pressure):
    """
    Envía los datos de temperatura, humedad y presión a ThingSpeak.
    
    :param temperature: Temperatura en grados Celsius.
    :param humidity: Humedad relativa en porcentaje.
    :param pressure: Presión atmosférica en hPa.
    """
    # Construir la URL para la solicitud HTTP GET
    url = f"{BASE_URL}?api_key={THINGSPEAK_API_KEY}&field1={temperature:.2f}&field2={humidity:.2f}&field3={pressure:.2f}"
    
    try:
        # Realizar la solicitud GET a ThingSpeak
        response = urequests.get(url)
        
        # Imprimir la respuesta de ThingSpeak
        #print(f"Respuesta de ThingSpeak: {response.text}")
        print("Datos enviados!")
        # Cerrar la respuesta para liberar recursos
        response.close()

    except Exception as e:
        print(f"Error al enviar datos a ThingSpeak: {e}")