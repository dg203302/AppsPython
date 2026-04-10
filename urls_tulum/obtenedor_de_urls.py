import json
from pathlib import Path

from playwright.sync_api import sync_playwright
latitud = -31.5375
longitud = -68.5364
timeout_default=3000
ACTION_TIMEOUT_MS = 15000
URL_mvit='https://moovitapp.com/tripplan/san_juan-6137/lines/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg'
lista_de_lineas = [
    "2", "3", "4", "20", "30", "40",
    "100", "101", "102", "103", "104",
    "120", "122", "123", "124", "125", "126", "127",
    "140", "141", "142",
    "160", "161", "162",
    "200", "201", "202", "203", "204", "205", "206", "207", "208", "209", "210", "211", "212","213", "214",
    "240", "241", "242", "243", "244", "245", "246",
    "260", "261", "262", "263", "264", "265", "266",
    "300", "301", "302", "303", "304", "305",
    "320", "321", "322", "323",
    "340", "341", "342", "343", "344", "345", "346",
    "360", "361", "362", "363", "364",
    "400", "401", "402", "403", "404", "405", "406", "407", "408",
    "420", "421", "422", "423",
    "440", "441", "442", "443", "444",
    "460", "461", "462",
    "500", "501", "502", "503", "504", "505",
    "560",
    "600", "601", "602",
    "700", "701", "702",
    "800", "801", "802", "808",
    "850",
    "A", "B", "C", "D", "E",
    "TEO1", "TEO2", "TEO3", "TNS",
]
urls_por_linea = {}
def _guardar_json(salida, data):
    salida.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    with sync_playwright() as motor:
        naveg = motor.chromium.launch(headless=False)
        contexto = naveg.new_context(
                geolocation={"latitude": latitud, "longitude": longitud},
                permissions=["geolocation"],
            )

        salida = Path(__file__).with_name("urls_por_linea.json")
        pag = contexto.new_page()
        try:
            pag.goto(URL_mvit, wait_until="domcontentloaded")
            pag.wait_for_timeout(timeout_default)
            buscador = pag.get_by_placeholder('Buscar una línea')
            buscador.wait_for(timeout=ACTION_TIMEOUT_MS)

            for linea in lista_de_lineas:
                try:
                    buscador.fill(linea)
                    buscador.press('Enter')
                    pag.wait_for_timeout(timeout_default)

                    primer_resultado = pag.locator('.line-item').first
                    primer_resultado.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
                    primer_resultado.click()
                    pag.wait_for_load_state("domcontentloaded")
                    pag.wait_for_timeout(timeout_default)

                    urls_por_linea[str(linea)] = pag.url
                except Exception:
                    urls_por_linea[str(linea)] = None

                _guardar_json(salida, urls_por_linea)

                pag.goto(URL_mvit, wait_until="domcontentloaded")
                pag.wait_for_timeout(timeout_default)
                buscador = pag.get_by_placeholder('Buscar una línea')
                buscador.wait_for(timeout=ACTION_TIMEOUT_MS)
        finally:
            pag.close()

        contexto.close()
        naveg.close()


if __name__ == "__main__":
    main()