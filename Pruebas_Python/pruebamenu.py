import requests
import time
API_URL = "https://proxyrt-production.up.railway.app/arrivals"

#API_URL = "http://0.0.0.0:8000/arrivals"
#API_URL = "https://proxy-rt.onrender.com/arrivals"
datos_consulta = {
    "url": "https://moovitapp.com/tripplan/san_juan-6137/lines/130/73818526/6607768/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
    "id_p": "stop-46329029-0"
}
print(f"Consultando a la Red Tulum para la línea {datos_consulta['url']}...")

try:
   
    respuesta = requests.post(API_URL, json=datos_consulta)

    respuesta.raise_for_status()

    datos_recibidos = respuesta.json()
    
    print("\n¡Respuesta exitosa!")
    print(f"Mensaje: {datos_recibidos.get('horario_estimado', 'Sin mensaje')}")
    print("Arribos:", datos_recibidos.get('arrivals', []))
    print(f"Tiempo de respuesta: {respuesta.elapsed.total_seconds():.2f} segundos")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Hubo un error de conexión: {e}")