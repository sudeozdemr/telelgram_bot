from turtle import update
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
import schedule
from telegram import Bot 

#Taking current date and time from server
now=datetime.now()
current_time=now.strftime("%Y-%m-%d %H:%M:%S")
reply_foto_url = 'https://www.komar.de/en/the-sea-view.html'

#Commands 
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE ):
    await update.message.reply_text('Hello Thanks for chatting with me! I am a telegram bot!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I am a telegram bot! Please type something so I can respond!')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command!')        

async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'{current_time}') 

async def send_image_command(update: Update, context: CallbackContext):
    await update.message.reply_photo(f'{reply_foto_url}') #await kullanmamızın amacı bu işlem yapılana kadar bekle demek.

def beep_command(chat_id) -> None:
    "Send the beep message."
    app.bot.send_message(chat_id, text='Beep!')

def set_timer_command(message):
    args = message.text.split()    
    if len(args) > 1 and args[1].isdigit():
        sec = int(args[1])
        schedule.every(sec).seconds.do(beep_command, message.chat.id).tag(message.chat.id)
    else: 
        app.reply_text(message, 'Usage: /set <seconds>')

def unset_timer_command(message):
    schedule.clear(message.chat.id)

#Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
         return 'Hey there!'
     
    if 'how are you' in processed:
         return 'I am good!'
     
    if 'I love python' in processed:
         return 'Remember to subscribe!'
    
    if 'sude' in processed:
        return 'I love youuuu <3'
    
    if 'please tell me the date' in processed:
        return f' the current date is {current_time} '
   
    if 'image' in processed:
        return f'{reply_foto_url}'

    return'I do not understant what you wrote...'

#handle_response fonksiyonu gelen metni işleyerek bir yanıt oluşturmayı sağlar.
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
    else:
         response: str = handle_response(text)
    print('Bot: ', response)
    await update.message.reply_text(response)
   
file=open("token.txt")
TOKEN=file.read().strip() #strip gereksiz boşlukları temizler.

async def error(update: update, context: ContextTypes.DEFAULT_TYPE):
     print(f'Update {update} caused error {context.error}')    

if __name__ == '__main__':#Bu kod bloğu python dosyasının doğrudan çalışıp çalışmadığını kontrol eder ve genelde kod bloğunun başında veya sonunda bulunur.
     print('Staring bot...') #Eğer dosya doğrudan çalışıyorsa yani başka bir dosyada içe aktarılmamışsa name özel değişkeni main olarak ayarlanır koşul doğrulanır ve blok yani telegram botu çalışır.
     app = Application.builder().token(TOKEN).build() #Blok içinde botun başlatılması ve çalıştırılması için gerekli kodlar bulunur. Telegram bot API ile bağlantı kurmak için uygulama oluşturulur. Oluşturulan uygulama tokeni kullnarak Telegram ile bağlantı kurar.
     print('Polling...')
     app.run_polling(poll_interval=5)

#Commands
app.add_handler(CommandHandler('start', start_command))
app.add_handler(CommandHandler('help', help_command))
app.add_handler(CommandHandler('custom', custom_command))
app.add_handler(CommandHandler('date', date_command))
app.add_handler(CommandHandler('image', send_image_command))
app.add_handler(CommandHandler('beep', beep_command))
app.add_handler(CommandHandler('set_timer', set_timer_command))
app.add_handler(CommandHandler('unset_timer', unset_timer_command))

#Messages
app.add_handler(MessageHandler(filters.TEXT, handle_message))

#Errors
app.add_error_handler(error)



