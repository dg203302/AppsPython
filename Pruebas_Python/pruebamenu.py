import requests

API_URL = "https://proxy-rt-api.onrender.com/arrivals"

datos_consulta = {
    "linea": "129",
    "parada": "Av. Ig. De La Roza y Los Jesuitas S -A"
}

print(f"Consultando a la Red Tulum para la línea {datos_consulta['linea']}...")

try:
   
    respuesta = requests.post(API_URL, json=datos_consulta)

    respuesta.raise_for_status()

    datos_recibidos = respuesta.json()
    
    print("\n¡Respuesta exitosa!")
    print(f"Mensaje: {datos_recibidos.get('message', 'Sin mensaje')}")
    print("Arribos:", datos_recibidos.get('arrivals', []))

except requests.exceptions.RequestException as e:
    print(f"\n❌ Hubo un error de conexión: {e}")