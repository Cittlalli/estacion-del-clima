def determinar_condiciones_climaticas(temperatura, humedad, presion):
    """Determina las condiciones climáticas según la temperatura, humedad y presión."""
    
    if presion < 1000 and humedad > 80:
        return "Posible tormenta o lluvia intensa"
    elif 1000 <= presion <= 1010 and humedad > 70:
        return "Posible lluvia ligera o cielo nublado"
    elif presion > 1015 and humedad < 60:
        return "Clima estable y despejado"
    elif humedad > 90 and (temperatura - punto_de_rocio(temperatura, humedad)) < 2:
        return "Posible niebla"
    elif temperatura > 35 and humedad < 40:
        return "Ola de calor"
    elif temperatura < 0 and presion > 1020:
        return "Posible ola de frío"
    elif presion < 995 and humedad > 85 and temperatura > 20:
        return "Posible tormenta eléctrica"
    elif presion < 980 and humedad > 85:
        return "Alerta de huracán o ciclón tropical"
    elif temperatura < 3 and presion > 1015 and humedad < 60:
        return "Posible helada nocturna"
    else:
        return "Condiciones normales"

def punto_de_rocio(temperatura, humedad):
    """Calcula el punto de rocío en función de la temperatura y la humedad."""
    import math
    b = 17.62
    c = 243.12
    gamma = (b * temperatura) / (c + temperatura) + math.log(humedad / 100.0)
    punto_rocio = (c * gamma) / (b - gamma)
    return punto_rocio

# Ejemplo de uso
temperatura = 25  # en grados Celsius
humedad = 85       # en porcentaje
presion = 995      # en hPa

condicion = determinar_condiciones_climaticas(temperatura, humedad, presion)
print("Condición climática:", condicion)
