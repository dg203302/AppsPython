import yt_dlp
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import subprocess
import platform
import os
from urllib.parse import urlparse, parse_qs

def es_playlist(url: str) -> bool:
    """Detecta si la URL es una lista de reproducción de YouTube"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return 'list' in query_params
    except:
        return False

def mostrar_dialog_playlist(app_window) -> str:
    """Muestra diálogo para elegir si descargar primer video o toda la lista"""
    # Crear ventana de diálogo personalizada
    dialog = ctk.CTkToplevel(app_window)
    dialog.geometry("400x200")
    dialog.title("Lista de Reproducción Detectada")
    dialog.resizable(False, False)
    dialog.attributes('-topmost', True)
    
    resultado = {"opcion": None}
    
    def seleccionar_primer():
        resultado["opcion"] = "primer"
        dialog.destroy()
    
    def seleccionar_lista():
        resultado["opcion"] = "lista"
        dialog.destroy()
    
    label = ctk.CTkLabel(
        dialog,
        text="Se detectó una lista de reproducción\n¿Qué deseas descargar?",
        font=("Arial", 13)
    )
    label.pack(pady=30)
    
    frame_botones = ctk.CTkFrame(dialog)
    frame_botones.pack(pady=20, padx=20, fill="x")
    
    boton_primer = ctk.CTkButton(
        frame_botones,
        text="🎥 Solo primer video",
        command=seleccionar_primer,
        height=35,
        fg_color="orange"
    )
    boton_primer.pack(side="left", padx=10, fill="both", expand=True)
    
    boton_lista = ctk.CTkButton(
        frame_botones,
        text="📂 Toda la lista",
        command=seleccionar_lista,
        height=35,
        fg_color="blue"
    )
    boton_lista.pack(side="left", padx=10, fill="both", expand=True)
    
    dialog.wait_window()
    return resultado["opcion"]

def DescargarVideo(URL:str, ubicacion_desc:str, opcion_playlist: str = "lista", formato: str = "video"):
    navs = ['chrome','firefox','brave','edge']
    url = URL
    
    # Si es una lista y el usuario eligió solo el primer video, extraer solo ese
    if opcion_playlist == "primer" and "list=" in url:
        # Remover parámetro de lista para descargar solo el video
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'list' in query_params:
            del query_params['list']
            # Reconstruir URL sin el parámetro 'list'
            new_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
            url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}{'?' + new_query if new_query else ''}"
    
    # Configurar opciones según formato
    if formato == "audio":
        formatoydl = 'bestaudio/best'
        extension = '%(title)s.%(ext)s'
    elif formato == "video":
        formatoydl = 'bestvideo+bestaudio/best'
        extension = '%(title)s.%(ext)s'
    else:
        formatoydl = 'bestvideo+bestaudio/best'
        extension = '%(title)s.%(ext)s'
    
    for nav in navs:
        ydl_opts = {
            'format': formatoydl,
            'cookiesfrombrowser': (nav,),
            'outtmpl': f'{ubicacion_desc}/{extension}'
        }
        # Agregar post-procesador para MP3 si es solo audio
        if formato == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"✓ Video(s) descargado(s) exitosamente en: {ubicacion_desc}")
            break
        except Exception as e:
            print(f"Navegador {nav} - Error: {e}")
            continue
# Variables globales
ruta_destino = ""
boton_abrir = None

def abrir_carpeta():
    """Abre la carpeta de destino en el explorador"""
    global ruta_destino
    if ruta_destino and os.path.exists(ruta_destino):
        if platform.system() == "Windows":
            os.startfile(ruta_destino)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", ruta_destino])
        else:  # Linux
            subprocess.Popen(["xdg-open", ruta_destino])

def seleccionar_ruta(label_ruta):
    """Abre diálogo para seleccionar carpeta de destino"""
    global ruta_destino
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta de destino")
    if carpeta:
        ruta_destino = carpeta
        label_ruta.configure(text=f"Ruta: {carpeta}")

def iniciar_descarga(url_entry, label_estado, frame_botones, app_window, var_formato):
    """Inicia la descarga en un hilo separado"""
    global ruta_destino, boton_abrir
    
    url = url_entry.get().strip()
    formato = var_formato.get()
    
    # Validaciones
    if not url:
        label_estado.configure(text="Error: Ingresa una URL", text_color="red")
        return
    
    if not ruta_destino:
        label_estado.configure(text="Error: Selecciona una carpeta", text_color="red")
        return
    
    # Detectar si es playlist y mostrar diálogo
    opcion_playlist = "lista"
    if es_playlist(url):
        opcion = mostrar_dialog_playlist(app_window)
        if opcion is None:
            label_estado.configure(text="Descarga cancelada", text_color="orange")
            return
        opcion_playlist = opcion
    
    # Cambiar estado a descargando
    label_estado.configure(text="Descargando...", text_color="yellow")
    
    # Limpiar botón anterior si existe
    for widget in frame_botones.winfo_children():
        widget.destroy()
    boton_abrir = None
    
    # Ejecutar descarga en un hilo separado
    def descargar():
        try:
            DescargarVideo(url, ruta_destino, opcion_playlist, formato)
            label_estado.configure(text="✓ Descarga completada", text_color="green")
            
            # Crear botón para abrir carpeta
            boton_abrir = ctk.CTkButton(
                frame_botones,
                text="📁 Abrir Carpeta",
                command=abrir_carpeta,
                height=35,
                fg_color="blue"
            )
            boton_abrir.pack(pady=10, padx=20, fill="x")
        except Exception as e:
            label_estado.configure(text=f"Error: {str(e)}", text_color="red")
    
    hilo = threading.Thread(target=descargar, daemon=True)
    hilo.start()

# Configurar tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Crear ventana principal
app = ctk.CTk()
app.geometry("500x550")
app.resizable(False,False)
app.title("YTDownloader")

# Título
titulo = ctk.CTkLabel(app, text="Descargar Video de YouTube", font=("Arial", 18, "bold"))
titulo.pack(pady=15)

# Frame para URL
frame_url = ctk.CTkFrame(app)
frame_url.pack(pady=15, padx=20, fill="x")

label_url = ctk.CTkLabel(frame_url, text="URL del video:", font=("Arial", 12))
label_url.pack(side="top", padx=5, pady=(0, 5))

url_entry = ctk.CTkEntry(frame_url, placeholder_text="Pega la URL del video aquí", width=400)
url_entry.pack(side="top", padx=5, fill="x", expand=False, ipady=8)

# Frame para carpeta
frame_carpeta = ctk.CTkFrame(app)
frame_carpeta.pack(pady=15, padx=20, fill="x")

boton_carpeta = ctk.CTkButton(
    frame_carpeta, 
    text="Seleccionar Carpeta", 
    command=lambda: seleccionar_ruta(label_ruta),
    width=150,
    height=35
)
boton_carpeta.pack(side="top", padx=5, pady=(0, 8))

label_ruta = ctk.CTkLabel(frame_carpeta, text="Ruta: No seleccionada", text_color="gray", font=("Arial", 10))
label_ruta.pack(side="top", padx=10, fill="x", expand=True)

# Frame para formato de descarga
frame_formato = ctk.CTkFrame(app)
frame_formato.pack(pady=15, padx=20, fill="x")

label_formato = ctk.CTkLabel(frame_formato, text="Formato:", font=("Arial", 12))
label_formato.pack(side="top", padx=5, pady=(0, 8))

var_formato = ctk.StringVar(value="video")

frame_radio = ctk.CTkFrame(frame_formato)
frame_radio.pack(side="top", fill="x")

radio_video = ctk.CTkRadioButton(
    frame_radio,
    text="🎬 Video + Audio",
    variable=var_formato,
    value="video"
)
radio_video.pack(side="left", padx=5)

radio_audio = ctk.CTkRadioButton(
    frame_radio,
    text="🎵 Solo Audio (MP3)",
    variable=var_formato,
    value="audio"
)
radio_audio.pack(side="left", padx=5)

# Botón de descarga
boton_descargar = ctk.CTkButton(
    app,
    text="Iniciar Descarga",
    command=lambda: iniciar_descarga(url_entry, label_estado, frame_botones, app, var_formato),
    height=40,
    font=("Arial", 12, "bold"),
    fg_color="green"
)
boton_descargar.pack(pady=20, padx=20, fill="x")

# Frame para botones dinámicos (abrir carpeta)
frame_botones = ctk.CTkFrame(app)
frame_botones.pack(pady=0, padx=20, fill="x")

# Label de estado
label_estado = ctk.CTkLabel(app, text="Listo", text_color="white", font=("Arial", 11))
label_estado.pack(pady=15)

app.mainloop()