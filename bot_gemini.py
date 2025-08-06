import logging
import datetime
import matplotlib.pyplot as plt
import io
import random
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ========= CONFIGURACIÓN =========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = "8356731546:AAE2hdD4puteeTjwuJCDkQ1TqP0LfBOl5wM"   # 👉 Reemplazá con tu token de BotFather
GEMINI_API_KEY = "AIzaSyADSNh95eDq9RQFOKhPUtnvlZzMfHUYn6A"      # 👉 Reemplazá con tu clave de Google AI Studio

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
modelo = genai.GenerativeModel("gemini-1.5-flash")

# ========= PLANES =========
plan_alimentacion = {
    "Desayuno": "Omelette de claras + avena",
    "Almuerzo": "Pechuga de pollo + ensalada cocida",
    "Merienda": "Yogur proteico + frutos secos",
    "Cena": "Pescado al horno + verduras al vapor"
}

plan_ejercicios = {
    "Lunes": "Cardio 30 min + Pesas 45 min",
    "Martes": "Descanso o yoga ligero",
    "Miércoles": "Cardio 30 min + Pesas 45 min",
    "Jueves": "Caminata 45 min",
    "Viernes": "Cardio 30 min + Pesas 45 min",
    "Sábado": "Actividad recreativa (bicicleta, nadar)",
    "Domingo": "Descanso"
}

pesos = {}
frases_motivacionales = [
    "¡Excelente trabajo! Cada paso cuenta 💪",
    "No te rindas, estás más cerca de tu meta 🚀",
    "Hoy es un gran día para mejorar tu salud 🥗",
    "¡Sigue así! La constancia es la clave 🔑",
    "Pequeños cambios hacen grandes resultados 🌟"
]

# ========= COMANDOS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de salud con Google Gemini AI listo.\nUsa /plan, /ejercicios, /peso, /grafico o escribime directo.")

async def mostrar_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "\n".join([f"{k}: {v}" for k,v in plan_alimentacion.items()])
    await update.message.reply_text(f"🍎 Tu plan de alimentación:\n{texto}")

async def mostrar_ejercicios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "\n".join([f"{k}: {v}" for k,v in plan_ejercicios.items()])
    await update.message.reply_text(f"💪 Plan de ejercicios:\n{texto}")

async def registrar_peso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        peso = float(context.args[0])
        fecha = datetime.date.today().strftime('%d-%m')
        user_id = update.effective_user.id
        if user_id not in pesos:
            pesos[user_id] = []
        pesos[user_id].append((fecha, peso))
        await update.message.reply_text(f"✅ Peso registrado: {peso} kg ({fecha})")
        await update.message.reply_text(random.choice(frases_motivacionales))
    except Exception:
        await update.message.reply_text("⚠️ Usa el formato: /peso 85.5")

async def grafico_peso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pesos or len(pesos[user_id]) < 2:
        await update.message.reply_text("Necesitas al menos 2 registros para ver el gráfico.")
        return
    fechas, valores = zip(*pesos[user_id])
    plt.figure()
    plt.plot(fechas, valores, marker='o')
    plt.title('Progreso de Peso')
    plt.xlabel('Fecha')
    plt.ylabel('Peso (kg)')
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await update.message.reply_photo(photo=buf)

# ========= RECORDATORIOS =========
async def recordatorio(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    hoy = datetime.date.today().strftime('%A')
    dias_map = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }
    dia_actual = dias_map.get(hoy, "Lunes")
    ejercicio_hoy = plan_ejercicios.get(dia_actual, "Descanso")
    mensaje = f"📅 Hoy es {dia_actual}.\n🍎 Alimentación: Usa /plan.\n💪 Ejercicio recomendado: {ejercicio_hoy}\n{random.choice(frases_motivacionales)}"
    await context.bot.send_message(job.chat_id, text=mensaje)

async def set_recordatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    context.job_queue.run_daily(recordatorio, time=datetime.time(hour=9, minute=0), chat_id=chat_id)
    context.job_queue.run_daily(recordatorio, time=datetime.time(hour=13, minute=0), chat_id=chat_id)
    context.job_queue.run_daily(recordatorio, time=datetime.time(hour=20, minute=0), chat_id=chat_id)
    await update.message.reply_text("✅ Recordatorios activados con alimentación y ejercicio dinámico.")

# ========= CHAT IA (GEMINI) =========
async def chat_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = modelo.generate_content(f"Eres un coach de salud motivador. Usuario: {user_message}")
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("❌ Error con la IA. Verifica tu API Key.")
        print("Error Gemini:", e)

# ========= EJECUCIÓN =========
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("plan", mostrar_plan))
app.add_handler(CommandHandler("ejercicios", mostrar_ejercicios))
app.add_handler(CommandHandler("peso", registrar_peso))
app.add_handler(CommandHandler("grafico", grafico_peso))
app.add_handler(CommandHandler("recordatorio", set_recordatorio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ia))

print("🤖 Bot corriendo con Google Gemini AI...")
app.run_polling()
