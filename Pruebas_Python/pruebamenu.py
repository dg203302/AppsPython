import requests

#API_URL = "https://proxy-rt-api-production.up.railway.app/arrivals"
API_URL = "http://0.0.0.0:8000/arrivals"
datos_consulta = {
    "url": "https://moovitapp.com/tripplan/san_juan-6137/lines/10/40197828/5701125/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
    "id_p": "stop-45379671-0"
}

print(f"Consultando a la Red Tulum para la línea {datos_consulta['url']}...")

try:
   
    respuesta = requests.post(API_URL, json=datos_consulta)

    respuesta.raise_for_status()

    datos_recibidos = respuesta.json()
    
    print("\n¡Respuesta exitosa!")
    print(f"Mensaje: {datos_recibidos.get('horario_estimado', 'Sin mensaje')}")
    print("Arribos:", datos_recibidos.get('arrivals', []))

except requests.exceptions.RequestException as e:
    print(f"\n❌ Hubo un error de conexión: {e}")