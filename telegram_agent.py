import os
import sys
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from core.config import setup_logging

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

active_process = None

# ADDED MIN_SALARY to states
KEYWORD, LOCATION, MIN_SALARY, SITES, COUNT = range(5)

async def start_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_process
    if active_process and active_process.returncode is None:
        await update.message.reply_text("?? A hunt is already running! Type /stop to cancel it first.")
        return ConversationHandler.END

    await update.message.reply_text("?? Waking up Ghost Agent.\n\n? Type the Job Role/Keyword (or type 'default'):")
    return KEYWORD

async def get_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['keyword'] = "L2 Application Support" if text.lower() == 'default' else text
    await update.message.reply_text("? Type the Target Location (or type 'default'):")
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['location'] = "Hyderabad" if text.lower() == 'default' else text
    
    # NEW QUESTION: Ask for minimum salary
    await update.message.reply_text("? Minimum Salary in LPA? (Type a number like 6, 8.5, or 'default'):")
    return MIN_SALARY

async def get_min_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Default to 6.0 if they type 'default'
    context.user_data['min_salary'] = "6.0" if text.lower() == 'default' else text
    
    await update.message.reply_text("? Sites to search? (naukri, indeed, glassdoor, foundit, all):")
    return SITES

async def get_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sites'] = update.message.text
    await update.message.reply_text("? Jobs to scan per site? (Enter a number):")
    return COUNT

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_process
    context.user_data['count'] = update.message.text
    
    kw = context.user_data['keyword']
    loc = context.user_data['location']
    min_sal = context.user_data['min_salary']
    sites = context.user_data['sites']
    count = context.user_data['count']
    
    await update.message.reply_text(f"?? Configuration locked:\n- Role: {kw}\n- Loc: {loc}\n- Min Pay: {min_sal} LPA\n- Sites: {sites}\n- Limit: {count}\n\nInitializing hunters. Live logs will appear here...")
    
    # Pass the new salary parameter to main.py
    active_process = await asyncio.create_subprocess_exec(
        sys.executable, 'main.py', 
        '--keyword', kw, 
        '--location', loc, 
        '--min_salary', min_sal,
        '--sites', sites, 
        '--count', str(count),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    buffer = []
    md_ticks = chr(96) * 3 

    async def send_updates():
        while active_process and active_process.returncode is None:
            await asyncio.sleep(4)
            if buffer:
                msg = "\n".join(buffer)
                buffer.clear()
                try:
                    if len(msg) > 4000: msg = msg[:4000] + "\n...[truncated]"
                    formatted_msg = md_ticks + "text\n" + msg + "\n" + md_ticks
                    await update.message.reply_text(formatted_msg, parse_mode="MarkdownV2")
                except: pass

    updater_task = asyncio.create_task(send_updates())

    while True:
        line = await active_process.stdout.readline()
        if not line: break
        decoded_line = line.decode('utf-8', errors='replace').strip()
        if decoded_line:
            print(decoded_line)
            safe_line = decoded_line.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
            buffer.append(safe_line)
            
    await active_process.wait()
    
    if buffer:
        msg = "\n".join(buffer)
        try: 
            formatted_msg = md_ticks + "text\n" + msg + "\n" + md_ticks
            await update.message.reply_text(formatted_msg, parse_mode="MarkdownV2")
        except: pass
            
    updater_task.cancel()
    if active_process.returncode == 0 or active_process.returncode is not None:
        if active_process.returncode != -15:
            await update.message.reply_text("? Campaign Cycle Complete. Agent returning to sleep.")
            
    active_process = None
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hunt configuration cancelled.")
    return ConversationHandler.END

async def stop_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_process
    if active_process and active_process.returncode is None:
        active_process.terminate()
        await update.message.reply_text("?? EMERGENCY STOP: Script terminated and browsers closed.")
    else:
        await update.message.reply_text("?? No active hunt running.")

if __name__ == '__main__':
    setup_logging()
    if not TOKEN:
        print("[-] TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and fill in your token.")
        sys.exit(1)
    print("?? Telegram Agent is online. Text /hunt to start, /stop to terminate.")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('stop', stop_hunt))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('hunt', start_hunt)],
        states={
            KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_keyword)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            MIN_SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_min_salary)], # NEW STATE
            SITES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sites)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()