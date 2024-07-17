from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests, logging, json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = open("token.txt").read().strip()

user_data = {}

scheduler = AsyncIOScheduler()

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! I'm a telegram bot, send me a  URL!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please send me a  Web-site URL.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    cancel_text = "Notifications are cancelled."
    if user_id in user_data:
        del user_data[user_id]
        scheduler.remove_job(str(user_id))
        await update.message.reply_text(cancel_text)
    else:
        await update.message.reply_text("You are not tracking any product.")

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"An error occurred: {context.error}")
    await update.message.reply_text("An error has occurred! Please try again later.")

'''async def send_notification(bot: Bot, user_id: int, message: str) -> None:
    await bot.send_message(chat_id=user_id, text=message)
'''

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
        price = price_tag.get_text() if price_tag else "Price couldn't found."
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return title, price, query_time, None

    except requests.exceptions.RequestException as e:
        return None, None, None, f"URL'den içerik alınırken hata oluştu: {e}"
    except AttributeError:
        return None, None, None, "Price couldn't found."

async def print_url_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id

    title, price, query_time, error = await fetch_url_info_command(url)

    if error:
        await update.message.reply_text(error)
    else:
        await update.message.reply_text(f"\n\nTitle: {title}\n\nPrice: {price}\n\nQuery_time: {query_time}")
        user_data[user_id] = {'url': url, 'last_price': price, 'query_time': query_time}
        
        if user_id not in user_data:
            # Kullanıcı bildirim sıklığını ayarlamadıysa varsayılan süreyi kullan
            scheduler.add_job(scheduled_task, IntervalTrigger(seconds=5), args=[bot], id=str(user_id))
        

async def scheduled_task(bot: Bot):
    current_time = datetime.now()

    print(f"---------------")

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
                await send_notification(bot, user_id, "Your tracking period has expired. You will no longer receive notifications for this URL.")
                continue

            title, current_price, query_time_str, error = await fetch_url_info_command(url)

            if error:
                logger.error(f"Error fetching URL info for user {user_id}: {error}")
                continue

            if current_price == last_price:
                message_equal = f"There is no change in the price of the product you are following: {last_price}"
                await send_notification(bot, user_id, message_equal)
            elif current_price < last_price:
                message_drop = f"The price of the product you are following has dropped!\nTitle: {title}\nOld Price: {last_price}\nNew Price: {current_price}"
                await send_notification(bot, user_id, message_drop)
            elif current_price > last_price:
                message_higher = f"The price of the product you are following has increased!\nTitle: {title}\nOld Price: {last_price}\nNew Price: {current_price}"
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


    # ErrorHandler
    application.add_error_handler(error_command)

    # Scheduler
    scheduler.start()
    scheduler.add_job(scheduled_task, IntervalTrigger(seconds=5), args=[bot], id=str(user_id))


    application.run_polling()

if __name__ == '__main__':
    main()
