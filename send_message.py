from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters 
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import requests, logging, asyncio, telegram
# Logging ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
TOKEN=open("token.txt").read().strip()

user_datas = {}

message = "Her 1 dakikada gönderilen otomatik mesaj." 
stop_message = "Artık her dakika mesaj almayacaksınız."
cancel_message = "Bildirimler iptal edildi."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_datas:
        #user_datas[user_id] = {"last_notified": None}
        user_datas[user_id] = {"registered_on": datetime.now()}
    registration_time = user_datas[user_id]["registered_on"]
    await update.message.reply_text(f'Your user ID is {user_id}.\nRegistered on: {registration_time}')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_datas:
        del user_datas[user_id]
        await update.message.reply_text(cancel_message)

async def send_notification(bot: Bot, user_id : int, message: str) -> None:
    await bot.send_message(chat_id=user_id, text = message)

async def scheduled_task(bot: Bot):
    for user_id in list(user_datas.keys()):
        if "registered_on" in user_datas[user_id]:
            registered_on = user_datas[user_id]["registered_on"]
            if datetime.now() - registered_on < timedelta(minutes=5):
                await send_notification(bot, user_id, message)
            else:
                await send_notification(bot , user_id, stop_message)
                del user_datas[user_id]

def main():
    # Application nesnesini oluşturma
    application = Application.builder().token(TOKEN).build()

    bot = Bot(token= TOKEN)

    # Komut işleyicilerini ekleme
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    #Sceduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_task, IntervalTrigger(minutes=1), args=[bot])
    scheduler.start()

    # Botu çalıştırma
    application.run_polling()

if __name__ == '__main__':
    main()
