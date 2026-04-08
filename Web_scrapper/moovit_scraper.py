import json
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
URL_mvit='https://moovitapp.com/tripplan/san_juan-6137/lines/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg'

cabecera_linea='.agency-header'
clase_linea_colect='.line-item'
#de 0 a 143 lineas de colectivo
clase_parada_colect='.stop-item'


latitud = -31.5375
longitud = -68.5364
ruta_carpeta_salida = Path("/home/dg/Documents/GitHub/AppsPython/Web_scrapper/Datos_scrappeados")
ruta_salida = ruta_carpeta_salida / "linearrival_data.jsonl"
delay_click_parada_ms = 5000
delay_carga_ui_ms = 1200
scroll_step_px = 500
scroll_micro_step_px = 100
scroll_micro_delay_ms = 220
scroll_post_delay_ms = 900
delay_entre_busqueda_lineas_ms = 1400
modo_solo_lineas = False
linea_actual = "sin_linea"
#se cargan todas

def capturar_requests(response):
    global linea_actual
    if "/api/lines/linearrival" in response.url and response.status == 200:
        try:
            datos = response.json()
            # Guardamos una respuesta por linea en formato JSONL para no perder capturas previas.
            with ruta_salida.open("a", encoding="utf-8") as archivo:
                registro = {
                    "linea": linea_actual,
                    "response_url": response.url,
                    "datos": datos,
                }
                archivo.write(json.dumps(registro, ensure_ascii=False))
                archivo.write("\n")
        except Exception as e:
            print(f"Error al intentar extraer el JSON: {e}")


def desplazar_suave(pagina, total_px=scroll_step_px):
    restante = max(total_px, 0)
    while restante > 0:
        paso = min(scroll_micro_step_px, restante)
        pagina.mouse.wheel(0, paso)
        pagina.wait_for_timeout(scroll_micro_delay_ms)
        restante -= paso

    pagina.wait_for_timeout(scroll_post_delay_ms)


def cargar_items_dinamicos(
    pagina,
    selector,
    pasos_max=80,
    pausa_ms=1400,
    estabilidad_objetivo=4,
    scroll_px=scroll_step_px,
):
    cantidad_previa = -1
    estabilidad = 0

    for _ in range(pasos_max):
        desplazar_suave(pagina, total_px=scroll_px)
        pagina.wait_for_timeout(pausa_ms)
        cantidad_actual = pagina.locator(selector).count()

        if cantidad_actual == cantidad_previa:
            estabilidad += 1
        else:
            estabilidad = 0
            cantidad_previa = cantidad_actual

        if estabilidad >= estabilidad_objetivo:
            break

    return pagina.locator(selector).count()


def recorrer_paradas_de_linea(pagina, etiqueta_linea):
    total_paradas = cargar_items_dinamicos(
        pagina,
        clase_parada_colect,
        pasos_max=50,
        pausa_ms=1200,
        estabilidad_objetivo=3,
        scroll_px=300,
    )
    print(f"Linea {etiqueta_linea}: {total_paradas} paradas detectadas")

    for indice_parada in range(total_paradas):
        paradas = pagina.locator(clase_parada_colect)
        if indice_parada >= paradas.count():
            break

        parada = paradas.nth(indice_parada)
        try:
            parada.scroll_into_view_if_needed(timeout=5000)
            parada.click(timeout=5000)
            print(f"  Parada {indice_parada + 1}/{total_paradas}")
            pagina.wait_for_timeout(delay_click_parada_ms)
        except PlaywrightTimeoutError:
            print(f"  Timeout en parada {indice_parada + 1}/{total_paradas}")
        except Exception as e:
            print(f"  Error en parada {indice_parada + 1}/{total_paradas}: {e}")


def volver_al_listado(pagina, url_listado):
    try:
        pagina.go_back(wait_until="domcontentloaded", timeout=10000)
    except PlaywrightTimeoutError:
        try:
            pagina.goto(url_listado, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            print(f"No se pudo volver al listado por timeout: {e}")
            return False
    except Exception as e:
        print(f"Error inesperado al volver al listado: {e}")
        return False

    try:
        pagina.wait_for_selector(clase_linea_colect, timeout=10000)
        pagina.wait_for_timeout(delay_carga_ui_ms)
        return True
    except Exception as e:
        print(f"No aparecio el listado de lineas al volver: {e}")
        return False


def recorrer_lineas_dinamicas(pagina):
    global linea_actual
    url_listado = pagina.url
    lineas_visitadas = set()
    rondas_sin_nuevas = 0
    max_rondas_sin_nuevas = 18

    while rondas_sin_nuevas < max_rondas_sin_nuevas:
        lineas_visibles = pagina.locator(clase_linea_colect)
        cantidad_visibles = lineas_visibles.count()
        nuevas_en_ronda = 0

        for indice_visible in range(cantidad_visibles):
            try:
                lineas_visibles = pagina.locator(clase_linea_colect)
                if indice_visible >= lineas_visibles.count():
                    break

                linea = lineas_visibles.nth(indice_visible)
                linea.scroll_into_view_if_needed(timeout=5000)
                texto_linea = linea.inner_text(timeout=3000).strip()
                href_linea = linea.get_attribute("href") or ""
                clave_linea = href_linea.strip() or texto_linea or f"linea_{indice_visible}"

                if clave_linea in lineas_visitadas:
                    continue

                linea_actual = clave_linea
                linea.click(timeout=5000)
                pagina.wait_for_timeout(delay_carga_ui_ms)
                lineas_visitadas.add(clave_linea)
                nuevas_en_ronda += 1
                print(f"Linea visitada: {clave_linea}")

                if not modo_solo_lineas:
                    recorrer_paradas_de_linea(pagina, clave_linea)

                if not volver_al_listado(pagina, url_listado):
                    pagina.goto(url_listado, wait_until="domcontentloaded", timeout=15000)
                    pagina.wait_for_selector(clase_linea_colect, timeout=10000)
                    pagina.wait_for_timeout(delay_carga_ui_ms)
            except PlaywrightTimeoutError:
                print(f"Timeout al abrir una linea visible (indice {indice_visible})")
                if not volver_al_listado(pagina, url_listado):
                    pagina.goto(url_listado, wait_until="domcontentloaded", timeout=15000)
                    pagina.wait_for_selector(clase_linea_colect, timeout=10000)
                    pagina.wait_for_timeout(delay_carga_ui_ms)
            except Exception as e:
                print(f"Error al abrir una linea visible (indice {indice_visible}): {e}")
                if not volver_al_listado(pagina, url_listado):
                    pagina.goto(url_listado, wait_until="domcontentloaded", timeout=15000)
                    pagina.wait_for_selector(clase_linea_colect, timeout=10000)
                    pagina.wait_for_timeout(delay_carga_ui_ms)

        if nuevas_en_ronda == 0:
            rondas_sin_nuevas += 1
            desplazar_suave(pagina, total_px=scroll_step_px * 2)
        else:
            rondas_sin_nuevas = 0

        desplazar_suave(pagina, total_px=scroll_step_px)
        pagina.wait_for_timeout(delay_entre_busqueda_lineas_ms)

    print(f"Total de lineas visitadas: {len(lineas_visitadas)}")

if __name__ == '__main__':
    ruta_carpeta_salida.mkdir(parents=True, exist_ok=True)

    if ruta_salida.exists():
        ruta_salida.unlink()

    with sync_playwright() as motor:
        naveg = motor.chromium.launch(headless=True)
        contexto = naveg.new_context(
            geolocation={"latitude": latitud, "longitude": longitud},
            permissions=["geolocation"],
        )
        pagina = contexto.new_page()
        #interceptacion de peticiones
        pagina.on("response", capturar_requests)
        #carga de pagina
        pagina.goto(URL_mvit)
        pagina.wait_for_timeout(3000)

        cargar_items_dinamicos(
            pagina,
            clase_linea_colect,
            pasos_max=40,
            pausa_ms=1400,
            estabilidad_objetivo=2,
        )
        print(f"Modo solo lineas: {modo_solo_lineas}")
        recorrer_lineas_dinamicas(pagina)

        naveg.close()