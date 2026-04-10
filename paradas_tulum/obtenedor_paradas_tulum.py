import json
from pathlib import Path

from playwright.sync_api import sync_playwright
latitud = -31.5375
longitud = -68.5364
timeout_default=3000
ACTION_TIMEOUT_MS = 15000

# Mapa: linea -> URL de la línea en Moovit
urls_por_linea = {
        "440-b": "https://moovitapp.com/tripplan/san_juan-6137/lines/440-b/70390902/6040975/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "440-c": "https://moovitapp.com/tripplan/san_juan-6137/lines/440-c/70390906/6040970/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "440-d": "https://moovitapp.com/tripplan/san_juan-6137/lines/440-d/72876318/6080275/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "441-b": "https://moovitapp.com/tripplan/san_juan-6137/lines/441-b/70390900/6040982/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "441-c": "https://moovitapp.com/tripplan/san_juan-6137/lines/441-c/70390899/6040971/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "441-d": "https://moovitapp.com/tripplan/san_juan-6137/lines/441-d/70390903/6040973/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
        "441-e": "https://moovitapp.com/tripplan/san_juan-6137/lines/441-e/70390901/6040972/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg",
}
Paradas_por_linea = {}
def _guardar_json(salida, data):
    salida.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extraer_paradas_con_id(pag):
    paradas = {}
    items = pag.locator('.stop-item').all()
    for item in items:
        nombre = item.locator('.title').inner_text().strip()
        stop_id = item.get_attribute('id')
        if not nombre:
            continue
        paradas[nombre] = stop_id
    return paradas


def main():
    with sync_playwright() as motor:
        naveg = motor.chromium.launch(headless=False)
        contexto = naveg.new_context(
                geolocation={"latitude": latitud, "longitude": longitud},
                permissions=["geolocation"],
            )

        salida = Path(__file__).with_name("paradas_por_linea.json")
        pag = contexto.new_page()
        try:
            for linea, url in urls_por_linea.items():
                try:
                    pag.goto(url, wait_until="domcontentloaded")
                    pag.wait_for_timeout(timeout_default)
                    pag.wait_for_selector('.stop-item', timeout=ACTION_TIMEOUT_MS)

                    Paradas_por_linea[str(linea)] = {
                        "linea": str(linea),
                        "paradas": _extraer_paradas_con_id(pag),
                    }
                except Exception:
                    Paradas_por_linea[str(linea)] = None

                _guardar_json(salida, Paradas_por_linea)
        finally:
            pag.close()

        contexto.close()
        naveg.close()


if __name__ == "__main__":
    main()