import flet as ft
def main(page: ft.Page):
    page.title = "Primera app usando Flet"
    texto = ft.Text("")
    def saludo(e):
        texto.value = "HOLA"
        page.update()
    boton = ft.ElevatedButton("Saludo", on_click=saludo)
    page.add(texto,boton)
ft.app(main)