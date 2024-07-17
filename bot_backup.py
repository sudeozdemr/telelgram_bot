from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests, logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = open("token.txt").read().strip()

user_data = {}
time_data = {}
default_interval_seconds = 20  

scheduler = AsyncIOScheduler()

SELECT_UNIT, INPUT_VALUE = range(2)

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! I'm a telegram bot, send me a Trendyol URL!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please send me a Trendyol Web-site URL.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    cancel_text = "Bildirimler iptal edildi."
    if user_id in user_data:
        del user_data[user_id]
        scheduler.remove_job(str(user_id))
        await update.message.reply_text(cancel_text)
    else:
        await update.message.reply_text("Takip ettiğiniz bir ürün bulunmuyor.")

async def density_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Hafta", "Gün", "Saat", "Dakika", "Saniye"]]
    await update.message.reply_text(
        "Lütfen bildirim almak istediğiniz zaman birimini seçin.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_UNIT

async def select_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    selected_unit = update.message.text
    time_data[user_id] = {"unit": selected_unit}
    await update.message.reply_text("Lütfen zaman birimi için bir sayı girin: ")
    return INPUT_VALUE

async def input_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    value = int(update.message.text)
    time_unit = context.user_data[user_id]['time_unit']

    if time_unit == "Hafta":
        interval = timedelta(weeks=value).total_seconds()
    elif time_unit == "Gün":
        interval = timedelta(days=value).total_seconds()
    elif time_unit == "Saat":
        interval = timedelta(hours=value).total_seconds()
    elif time_unit == "Dakika":
        interval = timedelta(minutes=value).total_seconds()
    elif time_unit == "Saniye":
        interval = timedelta(seconds=value).total_seconds()
    else:
        interval = default_interval_seconds

    context.user_data[user_id].update({'interval': interval, 'last_price': None})
    scheduler.add_job(
        scheduled_task,
        trigger=IntervalTrigger(seconds=interval),
        args=[user_id],
        id=str(user_id),
        replace_existing=True
    )
    await update.message.reply_text(f"Bildirim aralığı {value} {time_unit} olarak ayarlandı.")
    return ConversationHandler.END

def convert_to_seconds(unit: str, value: int) -> int:
    if unit == 'hafta':
        return value * 604800  # 7 days
    elif unit == 'gün':
        return value * 86400  # 24 hours
    elif unit == 'saat':
        return value * 3600  # 60 minutes
    elif unit == 'dakika':
        return value * 60  # 60 seconds
    elif unit == 'saniye':
        return value
    else:
        return 0

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"An error occurred: {context.error}")
    await update.message.reply_text("An error has occurred! Please try again later.")

async def send_notification(bot: Bot, user_id: int, message: str) -> None:
    await bot.send_message(chat_id=user_id, text=message)

async def fetch_url_info_command(url: str) -> tuple:
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        if "trendyol" in url:
            title = soup.find("title").get_text()
            price_tag = soup.find("span", class_="prc-dsc")
        elif "vatan" in url:
            title = soup.find("title").get_text()
            price_tag = soup.find("span", class_="product-list__price")
        else:
            return None, None, None, "Unsupported URL"

        title = soup.find("title").get_text()
        #price_tag = soup.find("span", class_="prc-dsc")
        price = price_tag.get_text() if price_tag else "Fiyat Bulunamadı"
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return title, price, query_time, None

    except requests.exceptions.RequestException as e:
        return None, None, None, f"URL'den içerik alınırken hata oluştu: {e}"
    except AttributeError:
        return None, None, None, "Fiyat bulunamadı"

async def print_url_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id

    title, price, query_time, error = await fetch_url_info_command(url)

    if error:
        await update.message.reply_text(error)
    else:
        await update.message.reply_text(f"\n\nTitle: {title}\n\nPrice: {price}\n\nQuery_time: {query_time}")
        user_data[user_id] = {'url': url, 'last_price': price, 'query_time': query_time}
        
        if user_id not in time_data:
            # Kullanıcı bildirim sıklığını ayarlamadıysa varsayılan süreyi kullan
            scheduler.add_job(scheduled_task, IntervalTrigger(seconds=default_interval_seconds), args=[bot], id=str(user_id))
        #else user_id in time_data:
            #scheduler.add_job(scheduled_task, IntervalTrigger(seconds=interval_seconds), args=[bot], id=str(user_id))

async def scheduled_task(bot: Bot):
    current_time = datetime.now()

    for user_id, data in list(user_data.items()):
        url = data['url']
        last_price = data['last_price']
        query_time_str = data["query_time"]

        try:
            if isinstance(query_time_str, str):
                query_time = datetime.strptime(query_time_str, "%Y-%m-%d %H:%M:%S")
            else:
                query_time = query_time_str

            if current_time - query_time > timedelta(minutes=1):
                del user_data[user_id]
                await send_notification(bot, user_id, "Takip süreniz doldu. Artık bu URL için bildirim almayacaksınız.")
                continue

            title, current_price, query_time_str, error = await fetch_url_info_command(url)

            if error:
                logger.error(f"Error fetching URL info for user {user_id}: {error}")
                continue

            if current_price == last_price:
                message_equal = f"Takip ettiğiniz ürünün fiyatında değişiklik yok: {last_price}"
                await send_notification(bot, user_id, message_equal)
            elif current_price < last_price:
                message_drop = f"Takip ettiğiniz ürünün fiyatı düştü!\nTitle: {title}\nOld Price: {last_price}\nNew Price: {current_price}"
                await send_notification(bot, user_id, message_drop)
            elif current_price > last_price:
                message_higher = f"Takip ettiğiniz ürünün fiyatı arttı!\nTitle: {title}\nOld Price: {last_price}\nNew Price: {current_price}"
                await send_notification(bot, user_id, message_higher)
                user_data[user_id]['last_price'] = current_price

        except Exception as e:
            logger.error(f"Error in scheduled task for user {user_id}: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    global bot
    bot = Bot(token=TOKEN)

    # CommandHandler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # MessageHandler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), print_url_info))

    # ConversationHandler for density_time_command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("density_time", density_time_command)],
        states={
            SELECT_UNIT: [MessageHandler(filters.TEXT & (~filters.COMMAND), select_unit)],
            INPUT_VALUE: [MessageHandler(filters.TEXT & (~filters.COMMAND), input_value)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    application.add_handler(conv_handler)

    # ErrorHandler
    application.add_error_handler(error_command)

    # Scheduler
    scheduler.start()

    application.run_polling()

if __name__ == '__main__':
    main()







   