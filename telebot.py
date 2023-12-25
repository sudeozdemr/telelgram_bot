
import telegram
import telegram.ext 
from telegram.ext import 
import telebot 
from telegram.ext import Updater, CommandHandler

with open("/Users/sudeozdemir/Desktop/Bit_Proj/token.txt","r") as token_file:
   TOKEN = token_file.read().strip() #strip boşlukları kaldırıyor, satır sonu düzenleme vs
def start(update, context):
   update.message.reply_text("Helloo! Welcome to the bot.")    

updater = Updater(TOKEN, use_context = True)
dp = updater.dispatcher

dp.add_handler(telegram.ext.CommandHandler("start", start))

updater.start_polling
updater.idle()

app = telegram.ext.Application.builder().token(TOKEN).build()
dispatcher =app.
dispatcher.add_handler(telegram.CommandHandler("start", start))

app.start_polling()


