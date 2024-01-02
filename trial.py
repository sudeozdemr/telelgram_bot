from turtle import update
from typing import Final

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import logging 

#Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(leveltime)s - %(message)s", level= logging.INFO)

#Commands 
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello Thanks for chatting with me! I am a telegram bot!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I am a telegram bot! Please type something so I can respond!')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command!')   

async def alarm_command(context: ContextTypes.DEFAULT_TYPE) -> None:
    job=context.job
    await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")    

def remove_job_if_exists_command(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def set_timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = float(context.args[0])
        if due < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")

async def unset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)

#Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    print('Random', processed)

    if 'hello' in processed:
        return 'Hey there!'

    if 'how are you' in processed:
        return 'I am good!'

    if 'I love python' in processed:
        return 'Remember to subscribe!'

    return'I do not understant what you wrote...'

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
    
async def error(update: update, context: ContextTypes.DEFAULT_TYPE):
     print(f'Update {update} caused error {context.error}')    

TOKEN ='6513847081:AAEjSnAE3vKOFuAQU2IMqfimyxGgRdzpCG4'

if __name__ == '__main__':
     print('Staring bot...')
     app = Application.builder().token(TOKEN).build()

#Commands
app.add_handler(CommandHandler('start', start_command))
app.add_handler(CommandHandler('help', help_command))
app.add_handler(CommandHandler('custom', custom_command))
app.add_handler(CommandHandler('help', alarm_command))
app.add_handler(CommandHandler('custom', remove_job_if_exists))
app.add_handler(CommandHandler('start', set_timer))
app.add_handler(CommandHandler('help', unset))


#Messages
app.add_handler(MessageHandler(filters.TEXT, handle_message))

#Errors
app.add_error_handler(error)

#Pols the bot
print('Polling...')
app.run_polling(poll_interval=3)