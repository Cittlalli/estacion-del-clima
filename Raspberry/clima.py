import time

def determinar_condiciones_climaticas(temperatura, humedad, presion, gradiente_presion=None, presion_anterior=None):
    """
    Determina la condición climática basada en temperatura, humedad, presión, 
    gradiente de presión y hora del día.

    Parámetros:
    - temperatura (float): Temperatura en grados Celsius.
    - humedad (float): Humedad relativa en porcentaje.
    - presion (float): Presión atmosférica en hPa.
    - gradiente_presion (float, opcional): Diferencia de presión reciente para detectar viento.
    - presion_anterior (float, opcional): Presión registrada anteriormente para calcular el gradiente si no se proporciona.

    Retorna:
    - str: Condición climática detectada (ej. "lluvia", "nublado", "despejado", etc.).
    """
    
    # Obtener la hora actual (formato 24h)
    hora = time.localtime().tm_hour

    # Calcular el gradiente de presión si no se proporcionó pero se tiene la presión anterior
    if gradiente_presion is None and presion_anterior is not None:
        gradiente_presion = presion_anterior - presion

    # Clasificación de condiciones según reglas heurísticas simples
    if humedad >= 80 and presion <= 1005:
        return "lluvia"
    elif 60 <= humedad < 80 and 1006 <= presion <= 1015:
        return "nublado"
    elif humedad < 60 and presion >= 1015 and temperatura >= 20:
        return "despejado"
    elif temperatura > 30:
        return "calor"
    elif temperatura < 10:
        return "frío"
    elif gradiente_presion is not None and abs(gradiente_presion) > 5:
        return "viento"
    elif hora >= 18 or hora < 6:
        return "normal_noche"
    else:
        return "normal_dia"
