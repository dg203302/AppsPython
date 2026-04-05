import yt_dlp as ytd

if __name__ == "__main__":
    url_video = input("URL del video para descargar: ").strip()

    if not url_video:
        print("No ingresaste una URL válida.")
    else:
        opts = {}
        with ytd.YoutubeDL(opts) as motor:
            print("Descargando...")
            motor.download([url_video])
            print("Listo")