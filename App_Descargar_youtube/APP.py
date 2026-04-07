import yt_dlp
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import threading
import subprocess
import platform
import os
from urllib.parse import urlparse, parse_qs
import time
import json
import re
from pathlib import Path

# Variables globales para control de descarga
descarga_activa = False
cancelar_descarga = False

# Archivo de configuración
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ytdownloader_config.json")

def guardar_configuracion(carpeta):
    """Guarda la configuración (última carpeta) en JSON"""
    try:
        config = {"ultima_carpeta": carpeta}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error al guardar configuración: {e}")

def cargar_configuracion():
    """Carga la configuración (última carpeta) desde JSON"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("ultima_carpeta", "")
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
    return ""

def validar_url_youtube(url: str) -> bool:
    """Valida que la URL sea de YouTube válida"""
    if not url.strip():
        return False
    
    # Patrones de URLs de YouTube válidas
    patrones_youtube = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie|youtube-kids)\.(com|be)/',
        r'(https?://)?youtu\.be/',
        r'(https?://)?(www\.)?youtube\.com/(watch|playlist)',
    ]
    
    return any(re.match(patron, url, re.IGNORECASE) for patron in patrones_youtube)

def obtener_opciones_formato(calidad: str):
    """Retorna las opciones de formato según la calidad seleccionada"""
    opciones = {
        "best": "bestvideo+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best",
        "360p": "bestvideo[height<=360]+bestaudio/best",
    }
    return opciones.get(calidad, "bestvideo+bestaudio/best")

def obtener_postprocessadores(formato: str):
    """Retorna postprocessadores según el formato seleccionado"""
    if formato == "audio":
        return [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    # Para video, FFmpeg combina automáticamente a MP4
    return []

class SpinnerIOS(ctk.CTkFrame):
    """Spinner estilo iOS con animación circular"""
    def __init__(self, parent, size=50, color="white", **kwargs):
        super().__init__(parent, **kwargs)
        self.size = size
        self.color = color
        self.angle = 0
        self.animando = False
        
        # Canvas para el spinner
        self.canvas = Canvas(
            self,
            width=size,
            height=size,
            bg=self._apply_appearance_mode(("white", "black")),
            highlightthickness=0
        )
        self.canvas.pack()
        
    def iniciar(self):
        """Inicia la animación del spinner"""
        self.animando = True
        self._animar()
    
    def detener(self):
        """Detiene la animación del spinner"""
        self.animando = False
    
    def _animar(self):
        """Anima el spinner"""
        if not self.animando:
            return
        
        self.canvas.delete("all")
        
        # Dibujar círculo base
        centro_x = self.size / 2
        centro_y = self.size / 2
        radio = self.size / 2 - 4
        
        # Crear efecto de rotación con líneas
        num_lineas = 12
        for i in range(num_lineas):
            angle = (i * 30 + self.angle) % 360
            angle_rad = angle * 3.14159 / 180
            
            # Opacidad decrece de adentro hacia afuera
            opacidad = int(255 * (1 - i / num_lineas))
            color_hex = f"#{opacidad:02x}{opacidad:02x}{opacidad:02x}"
            
            x1 = centro_x + radio * 0.6 * (i % 2 == 0 and 0.8 or 0.5)
            y1 = centro_y + radio * 0.6 * (i % 2 == 0 and 0.8 or 0.5)
            
            # Puntos del arco
            import math
            x1 = centro_x + (radio * 0.7) * math.cos(angle_rad)
            y1 = centro_y + (radio * 0.7) * math.sin(angle_rad)
            x2 = centro_x + radio * math.cos(angle_rad)
            y2 = centro_y + radio * math.sin(angle_rad)
            
            brightness = int(100 + 155 * (1 - i / num_lineas))
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=f"#{brightness:02x}{brightness:02x}{brightness:02x}",
                width=2
            )
        
        self.angle = (self.angle + 30) % 360
        self.after(50, self._animar)

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

def DescargarVideo(URL:str, ubicacion_desc:str, opcion_playlist: str = "lista", formato: str = "video", calidad: str = "best"):
    global cancelar_descarga
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
        formatoydl = obtener_opciones_formato(calidad)
        extension = '%(title)s.mp4'
    else:
        formatoydl = obtener_opciones_formato(calidad)
        extension = '%(title)s.mp4'
    
    for nav in navs:
        if cancelar_descarga:
            raise Exception("Descarga cancelada por el usuario")
        
        ydl_opts = {
            'format': formatoydl,
            'cookiesfrombrowser': (nav,),
            'outtmpl': f'{ubicacion_desc}/{extension}',
            'postprocessors': obtener_postprocessadores(formato),
            'merge_output_format': 'mp4' if formato == "video" else None,
        }
        
        # Remover None values
        ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Hook para detectar cancelación durante la descarga
                def progress_hook(d):
                    if cancelar_descarga:
                        raise Exception("Descarga cancelada por el usuario")
                
                ydl.add_progress_hook(progress_hook)
                ydl.download([url])
            print(f"✓ Video(s) descargado(s) exitosamente en: {ubicacion_desc}")
            break
        except Exception as e:
            if "cancelada" in str(e).lower():
                raise
            print(f"Navegador {nav} - Error: {e}")
            continue
# Variables globales
ruta_destino = ""
boton_abrir = None
spinner_actual = None
frame_spinner = None
frame_botones = None

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
        guardar_configuracion(carpeta)
        label_ruta.configure(text=f"Ruta: {carpeta}", text_color="green")

def pegar_del_portapapeles(url_entry):
    """Pega el contenido del portapapeles en el campo de URL"""
    try:
        # Obtener contenido del portapapeles
        contenido = app.clipboard_get()
        # Limpiar el campo y pegar
        url_entry.delete(0, "end")
        url_entry.insert(0, contenido)
    except Exception as e:
        print(f"Error al acceder al portapapeles: {e}")

def limpiar_url(url_entry):
    """Limpia el campo de URL"""
    url_entry.delete(0, "end")
    url_entry.focus()

def cancelar_descarga_actual():
    """Cancela la descarga en curso"""
    global cancelar_descarga, descarga_activa, spinner_actual, frame_spinner, frame_botones
    cancelar_descarga = True
    descarga_activa = False
    
    # Detener spinner
    if spinner_actual:
        spinner_actual.detener()
    
    # Limpiar contenedores
    if frame_spinner:
        for widget in frame_spinner.winfo_children():
            widget.destroy()
    
    if frame_botones:
        for widget in frame_botones.winfo_children():
            widget.destroy()

def iniciar_descarga(url_entry, label_estado, frame_botones_param, app_window, var_formato, frame_spinner_param, var_calidad=None):
    """Inicia la descarga en un hilo separado"""
    global ruta_destino, boton_abrir, cancelar_descarga, descarga_activa, spinner_actual, frame_spinner, frame_botones
    
    # Asignar parámetros a variables globales
    frame_spinner = frame_spinner_param
    frame_botones = frame_botones_param
    
    url = url_entry.get().strip()
    formato = var_formato.get()
    calidad = var_calidad.get() if var_calidad else "best"
    
    # Validaciones
    if not url:
        label_estado.configure(text="Error: Ingresa una URL", text_color="red")
        return
    
    # Validar que sea una URL de YouTube
    if not validar_url_youtube(url):
        label_estado.configure(text="Error: La URL no es de YouTube válida", text_color="red")
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
    
    # Reiniciar variables de control
    cancelar_descarga = False
    descarga_activa = True
    
    # Limpiar widgets anteriores
    for widget in frame_botones.winfo_children():
        widget.destroy()
    for widget in frame_spinner.winfo_children():
        widget.destroy()
    boton_abrir = None
    
    # Mostrar spinner
    spinner_actual = SpinnerIOS(frame_spinner, size=50, fg_color="transparent")
    spinner_actual.pack(pady=10)
    spinner_actual.iniciar()
    
    # Crear botón cancelar
    boton_cancelar = ctk.CTkButton(
        frame_botones,
        text="🛑 Cancelar Descarga",
        command=cancelar_descarga_actual,
        height=35,
        fg_color="red"
    )
    boton_cancelar.pack(pady=10, padx=20, fill="x")
    
    label_estado.configure(text="", text_color="white")
    
    # Ejecutar descarga en un hilo separado
    def descargar():
        global cancelar_descarga, descarga_activa, spinner_actual, frame_spinner, frame_botones
        try:
            DescargarVideo(url, ruta_destino, opcion_playlist, formato, calidad)
            
            # Detener y limpiar spinner
            if spinner_actual:
                spinner_actual.detener()
            
            # Limpiar frame del spinner
            for widget in frame_spinner.winfo_children():
                widget.destroy()
            
            label_estado.configure(text="✓ Descarga completada", text_color="green")
            
            # Limpiar botones anteriores
            for widget in frame_botones.winfo_children():
                widget.destroy()
            
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
            # Detener spinner
            if spinner_actual:
                spinner_actual.detener()
            
            # Limpiar frame del spinner
            for widget in frame_spinner.winfo_children():
                widget.destroy()
            
            error_msg = str(e)
            if "cancelada" in error_msg.lower():
                label_estado.configure(text="⛔ Descarga cancelada", text_color="orange")
            else:
                label_estado.configure(text=f"Error: {error_msg}", text_color="red")
            
            # Limpiar botones
            for widget in frame_botones.winfo_children():
                widget.destroy()
        
        finally:
            descarga_activa = False
    
    hilo = threading.Thread(target=descargar, daemon=True)
    hilo.start()

# Configurar tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Crear ventana principal
app = ctk.CTk()
app.geometry("600x750")
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

# Frame para el entry y botones
frame_url_entrada = ctk.CTkFrame(frame_url)
frame_url_entrada.pack(side="top", fill="x", expand=True)

url_entry = ctk.CTkEntry(frame_url_entrada, placeholder_text="Pega la URL del video aquí", width=400)
url_entry.pack(side="left", padx=(5, 0), fill="x", expand=True, ipady=8)

boton_pegar = ctk.CTkButton(
    frame_url_entrada,
    text="📋 Pegar",
    command=lambda: pegar_del_portapapeles(url_entry),
    width=60,
    height=35
)
boton_pegar.pack(side="left", padx=5)

boton_limpiar = ctk.CTkButton(
    frame_url_entrada,
    text="🗑️ Limpiar",
    command=lambda: limpiar_url(url_entry),
    width=60,
    height=35
)
boton_limpiar.pack(side="left", padx=(5, 5))

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

# Cargar última carpeta guardada
ruta_destino = cargar_configuracion()
if ruta_destino and os.path.exists(ruta_destino):
    label_ruta = ctk.CTkLabel(frame_carpeta, text=f"Ruta: {ruta_destino}", text_color="green", font=("Arial", 10))
else:
    ruta_destino = ""
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

# Frame para calidad de descarga
frame_calidad = ctk.CTkFrame(app)
frame_calidad.pack(pady=15, padx=20, fill="x")

label_calidad = ctk.CTkLabel(frame_calidad, text="Calidad de Video:", font=("Arial", 12))
label_calidad.pack(side="top", padx=5, pady=(0, 8))

var_calidad = ctk.StringVar(value="best")

frame_radio_calidad = ctk.CTkFrame(frame_calidad)
frame_radio_calidad.pack(side="top", fill="x")

radio_best = ctk.CTkRadioButton(
    frame_radio_calidad,
    text="⭐ Mejor Calidad",
    variable=var_calidad,
    value="best"
)
radio_best.pack(side="left", padx=5)

radio_1080 = ctk.CTkRadioButton(
    frame_radio_calidad,
    text="🎬 1080p",
    variable=var_calidad,
    value="720p"
)
radio_1080.pack(side="left", padx=5)

radio_480 = ctk.CTkRadioButton(
    frame_radio_calidad,
    text="📺 480p",
    variable=var_calidad,
    value="480p"
)
radio_480.pack(side="left", padx=5)

radio_360 = ctk.CTkRadioButton(
    frame_radio_calidad,
    text="📱 360p",
    variable=var_calidad,
    value="360p"
)
radio_360.pack(side="left", padx=5)

# Botón de descarga
boton_descargar = ctk.CTkButton(
    app,
    text="Iniciar Descarga",
    command=lambda: iniciar_descarga(url_entry, label_estado, frame_botones, app, var_formato, frame_spinner, var_calidad),
    height=40,
    font=("Arial", 12, "bold"),
    fg_color="green"
)
boton_descargar.pack(pady=20, padx=20, fill="x")

# Frame para el spinner
frame_spinner = ctk.CTkFrame(app)
frame_spinner.pack(pady=5, padx=20, fill="x")

# Frame para botones dinámicos (abrir carpeta, cancelar)
frame_botones = ctk.CTkFrame(app)
frame_botones.pack(pady=0, padx=20, fill="x")

# Label de estado
label_estado = ctk.CTkLabel(app, text="Listo", text_color="white", font=("Arial", 11))
label_estado.pack(pady=15)

app.mainloop()