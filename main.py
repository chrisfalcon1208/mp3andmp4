from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters,
)
import yt_dlp
import os
import imageio_ffmpeg as ffmpeg

# Ruta para guardar los archivos temporalmente
TEMP_DIR = "downloads"

# Comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Envíame un enlace de YouTube y te preguntaré si deseas descargar en formato MP3 o MP4.")

# Manejar enlaces de YouTube y mostrar opciones
async def ask_format(update: Update, context: CallbackContext):
    url = update.message.text
    context.user_data['url'] = url  # Guardar el enlace en datos del usuario

    # Crear botones para elegir el formato
    keyboard = [
        [
            InlineKeyboardButton("MP3", callback_data="mp3"),
            InlineKeyboardButton("MP4", callback_data="mp4"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("¿En qué formato deseas descargar?", reply_markup=reply_markup)

# Descargar en el formato seleccionado
async def download_file(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    format_choice = query.data  # "mp3" o "mp4"
    url = context.user_data.get('url')  # Recuperar el enlace guardado
    await query.edit_message_text(f"Descargando en formato {format_choice.upper()}... Esto puede tardar un poco.")

    try:
        # Configuración de yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best' if format_choice == "mp3" else 'bestvideo+bestaudio[ext=mp4]/mp4',
            'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4' if format_choice == "mp4" else None,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                } if format_choice == "mp3" else {
                    'key': 'FFmpegEmbedSubtitle',  # Opcional para videos con subtítulos
                }
            ],
            'ffmpeg_location': ffmpeg.get_ffmpeg_exe(),  # Usa la versión empaquetada de ffmpeg
            'postprocessor_args': ['-movflags', '+faststart'],  # Optimiza archivos MP4 para streaming
        }

        # Descargar y convertir si es necesario
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_extension = "mp3" if format_choice == "mp3" else "mp4"
            file_name = ydl.prepare_filename(info).rsplit('.', 1)[0] + f".{file_extension}"
        
        # Enviar el archivo al usuario
        with open(file_name, 'rb') as file:
            if format_choice == "mp3":
                await query.message.reply_audio(file)
            else:
                await query.message.reply_video(file)

        # Limpiar archivos temporales
        os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"Hubo un error: {str(e)}")

# Configurar el bot
def main():
    # Reemplaza con tu token
    TOKEN = "7551784511:AAHAD_frpzi1AxbZR7vV4nC45npMemRZV1U"
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Configurar la aplicación del bot
    application = Application.builder().token(TOKEN).build()

    # Manejar comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_format))
    application.add_handler(CallbackQueryHandler(download_file))

    # Iniciar el bot
    application.run_polling()

if __name__ == '__main__':
    main()
