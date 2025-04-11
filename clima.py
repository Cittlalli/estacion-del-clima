import time

def determinar_condiciones_climaticas(temperatura, humedad, presion, gradiente_presion=None, presion_anterior=None)
    hora = time.localtime().tm_hour
     # Si no se tiene el gradiente directo pero se dispone de la presión anterior, se calcula el gradiente.
    if gradiente_presion is None and presion_anterior is not None:
        gradiente_presion = presion_anterior - presion

    # Evaluar condiciones específicas
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
    # Evaluación de la condición de viento usando el gradiente (valor absoluto)
    elif gradiente_presion is not None and abs(gradiente_presion) > 5:
        return "viento"
    elif hora >= 18 or hora < 6:
        return "normal_noche"
    else:
        return "normal_dia"