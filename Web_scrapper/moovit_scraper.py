import json
from pathlib import Path

from playwright.sync_api import sync_playwright
URL_mvit='https://moovitapp.com/tripplan/san_juan-6137/lines/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg'

cabecera_linea='.agency-header'
clase_linea_colect='.line-item'
#de 0 a 143 lineas de colectivo
clase_parada_colect='.stop-item'


latitud = -31.5375
longitud = -68.5364
ruta_salida = Path(__file__).resolve().parent / "linearrival_data.json"
#se cargan todas

def capturar_requests(response):
    if "/api/lines/linearrival" in response.url and response.status == 200:
        try:
            datos = response.json()
            with ruta_salida.open("w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al intentar extraer el JSON: {e}")

if __name__ == '__main__':
    with sync_playwright() as motor:
        naveg = motor.chromium.launch(headless=False)
        contexto = naveg.new_context(
            geolocation={"latitude": latitud, "longitude": longitud},
            permissions=["geolocation"],
        )
        pagina = contexto.new_page()
        #interceptacion de peticiones
        pagina.on("response", capturar_requests)
        #carga de pagina
        pagina.goto(URL_mvit)
        #lista de lineas y paradas 
        lista_de_colects = pagina.locator(clase_linea_colect)
        print(lista_de_colects.count())
        lista_de_colects.first.click()
        lista_de_parads = pagina.locator(clase_parada_colect)
        lista_de_parads.first.click()
        pagina.wait_for_timeout(5000)

        naveg.close()