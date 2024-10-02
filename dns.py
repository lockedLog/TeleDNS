from typing import Final, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, filters, ContextTypes, MessageHandler
import dns.resolver
import whois
import json
import os
import requests

with open('botToken.txt','r') as t:
    TOKEN = t.read()


user_preferences: Dict[int, str] = {}

def getDNS(domain):
    record_types = ['A', 'AAAA', 'NS', 'CNAME', 'MX', 'PTR', 'SOA', 'TXT']
    success = []

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for server in answers:
                success.append(f'{record_type}: {server.to_text()}')
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass

    return '\n'.join(success) if success else 'No information available.'

def getWHO(domain):
    who = whois.whois(domain)
    return str(who)

def getStatus(domain):
    try: 
        check = requests.get(f'https://www.'+ domain)
        if check.status_code == 200:
            return 'Server is online and functioning.'
    except:
        return 'Server is offline or is not functioning.'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the multifunctioning Domain Tool")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands: \n\n"
        "DNS - Returns A, NS, MX, TXT, and more records.\n>> Format: !dns domainhere\n\n"
        "WHOIS - Returns register, creation/expiration dates, more name servers, status, emails, location.\n>> Format: !whois domainhere\n\n"
        "OUTPUT - Set preferred output format (txt or json (using messages by default)).\n>> Format: !output format"
        "STATUS - Returns the current status of a website (Online or Offline).\n>> Format: !status domainhere"
    )

async def output_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    text = update.message.text.lower()

    preferred_format = text.split('!output ', 1)[1].strip()
    if preferred_format in ['txt', 'json', 'html']:
        user_preferences[user_id] = preferred_format
        await update.message.reply_text(f"{preferred_format.upper()} saved as your preferred output.")
    else:
        await update.message.reply_text('Using messages by default.')

def handle_response(user_id: int, text: str) -> str:
    processed = text.lower()

    if '!dns' in processed:
        domain = processed.split('!dns ', 1)[1].strip()
        return getDNS(domain)

    elif '!whois' in processed:
        domain = processed.split('!whois ', 1)[1].strip()
        return getWHO(domain)
    
    elif '!status' in processed:
        domain = processed.split('!status ', 1)[1].strip()
        return getStatus(domain)

    return 'No command recognized or invalid format.'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    text = update.message.text
    print(f'User ({user_id}) sent: {text}')

    if text.lower().startswith('!output'):
        await output_command(update, context)
        return

    response = handle_response(user_id, text)
    preferred_format = user_preferences.get(user_id, 'messages')

    if preferred_format == 'messages':
        await update.message.reply_text(response)
    else:

        file_name = 'info.txt' if preferred_format == 'txt' else 'info.json'
        if preferred_format == 'txt':
            file_content = response
        elif preferred_format == 'json':
            file_content = json.dumps({'response': response}, indent=4)
        
        with open(file_name, 'w') as file:
            file.write(file_content)
        
        await update.message.reply_document(document=open(file_name, 'rb'))
        os.remove(file_name)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('- DNS Bot -')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('Bot is online and awaiting messages.')
    app.run_polling(poll_interval=2)