from playwright.sync_api import sync_playwright
latitud = -31.5375
longitud = -68.5364
timeout_default=1000
URl_mvt= 'https://moovitapp.com/tripplan/san_juan-6137/lines/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg'

linea_p = input("linea")
parada_p = input("parada")
with sync_playwright() as motor:
    naveg = motor.chromium.launch(headless=False)
    contexto = naveg.new_context(
            geolocation={"latitude": latitud, "longitude": longitud},
            permissions=["geolocation"],
        )
    pag=contexto.new_page()
    pag.goto(f'https://moovitapp.com/tripplan/san_juan-6137/lines/{linea_p}/es-419?customerId=NPIdiV-P9Gcj-pA7yOXVPg')
    pag.wait_for_timeout(timeout_default)

    with pag.expect_response(
        lambda response: "/api/lines/linearrival" in response.url and response.status == 200
    ) as inf_resp:
        pag.locator('.title').filter(has_text=parada_p).click()
        pag.wait_for_timeout(timeout_default)
    try:
        datos = inf_resp.value.json()
        if not datos[0].get("arrivals"):
            elem = pag.locator("div.current.ng-star-inserted span.ng-star-inserted").first
            print(elem.inner_text().strip())
        else:
            print(datos)
    except Exception as e:
        print(f"Error al intentar extraer el JSON: {e}")

    pag.close()


#datos de prueba
#linea_p='129'
#parada_p='Av. Ig. De La Roza y Los Jesuitas S -A'