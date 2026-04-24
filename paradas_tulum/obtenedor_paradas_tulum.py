import json
from pathlib import Path

from playwright.sync_api import sync_playwright
latitud = -31.5375
longitud = -68.5364
timeout_default=5000
ACTION_TIMEOUT_MS = 15000
numeros_de_lineas = [
    "130"
]
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
            for linea in numeros_de_lineas:
                try:
                    pag.goto('https://moovitapp.com/tripplan/san_juan-6137/lines/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg')
                    pag.wait_for_timeout(timeout_default)
                    buscador = pag.get_by_placeholder('Buscar una línea')
                    buscador.fill(linea)
                    buscador.press('Enter')
                    pag.wait_for_timeout(timeout_default)
                    pag.locator('.line-item').first.click()
                    pag.wait_for_timeout(timeout_default)
                    dropdown = pag.locator('button.lines-dropdown')
                    if dropdown.count() > 0:
                        # Abrir el menú una vez para contar las opciones
                        dropdown.click()
                        pag.wait_for_timeout(2000)
                        count = pag.locator('[role="menuitem"]').count()
                        # Cerrar el menú
                        pag.keyboard.press('Escape')
                        pag.wait_for_timeout(1000)

                        for i in range(count):
                            # Abrir el menú de nuevo para cada opción
                            dropdown.click()
                            pag.wait_for_timeout(2000)
                            opciones = pag.locator('[role="menuitem"]')
                            nombre_opcion = opciones.nth(i).inner_text().strip()
                            opciones.nth(i).click()
                            pag.wait_for_timeout(timeout_default)
                            pag.wait_for_selector('.stop-item', timeout=ACTION_TIMEOUT_MS)
                            clave = f"{linea}_opcion_{i}"
                            Paradas_por_linea[clave] = {
                                "linea": str(linea),
                                "opcion": nombre_opcion,
                                "paradas": _extraer_paradas_con_id(pag),
                            }
                    else:
                        # Sin menú de direcciones, extraer directamente
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