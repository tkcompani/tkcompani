import telegram
import logging
import random
import requests
import langdetect
import datetime
import pysqlite3 as sqlite3
import uuid

from telegram import Update, ChatMemberUpdated
from telegram.ext import CallbackContext, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ChatMemberHandler
from datetime import time


#logs
logging.basicConfig(level=logging.INFO)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  level=logging.DEBUG)

logger = logging.getLogger(__name__)


#Database - db
conn = sqlite3.connect('brothers.db')

c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS brothers (

          first_name text,
          sur_name text,
          username blob,
          phone_no integer,
          id blob
          )
          """)
          
brothers = []



#detecting Language with LangDetect
def detect_language(input_text):
    try:
        language = langdetect.detect(input_text)
        return language
    except langdetect.lang_detect_exception.LangDetectException:
        return 'en'


#making translation request function
class Translator:
    def __init__(self, to_lang):
        self.to_lang = to_lang
        self.url = f"https://api.mymemory.translated.net/get?q=Hello World!&langpair=en|{to_lang}"
        self.session = requests.Session()

    def _make_request(self, text):
        try:
            response = self.session.get(self.url, params={'q': text, 'lang': self.to_lang})
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f'error:{e}')
            return None

    def translate_text(self, input_text, detected_language):
        data = self._make_request(input_text)
        try:
            if data is not None:
                return data['responseData']['translatedText']
            else:
                return None
        except Error as e:
            logging.ERROR('{e}')





#Commands
##Start command
async def start(update: Update, context: CallbackContext):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, how can can I help, use /help for more info.")

        
##about cmd
async def about_us(update: Update, context: CallbackContext):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Know the purpose, goal and more <a href='https://brotherscommunityonline.wordpress.com/about-us/'>About us</a>", parse_mode='HTML')

    
##Help command
async def help(update: Update, context: CallbackContext):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Below are available commands.\nUse them to interact with me:\n/start - start brother bot\n/help - get more info\n/join_online - join the community online and make a profile\n/translate - translate words in English lang to the other langs\n/my_account - get your online community or telegram account profile details\n/about_us - know our goal. \n\n[V1.00.1]")
    
##join brothers online
async def join_online(update: Update, context: CallbackContext):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Join the Brothers International Community online <a href='https://brotherscommmunity.online/'>Online</a>", parse_mode="HTML")


###Some specific functions also cmds
##Translation func cmd
async def trans_cmd(update: Update, context: CallbackContext):
    
    #from_lang = context.args[0]
    to_lang = context.args[0]
    user_input = context.args[1]
    
    translator = Translator(to_lang = to_lang)
    detected_language = detect_language(user_input)
    translated_text = translator.translate_text(user_input, detected_language)
    
    
    try:
        if context.args == '' or to_lang == "" or user_input == "":
            await context.bot.send_message(chat_id=update.effective_chat.id, text='please use format.../cmd language(code) text_to_translate')
        else:             
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Translated text: \n{translated_text}")
    
    except IndexError:
        return await context.bot.send_message(chat_id=update.effective_chat.id, text='please use format.../cmd language(code) text_to_translate')
        

##Register Account cmd
async def register(update: Update, context: CallbackContext):
    
    if len(context.args) < 3:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Invalid usage! Use: /register first_name surname phone_number"
        )
        return
    
    first_name = context.args[0]
    surname = context.args[1]
    phone_no = context.args[2]
    username = update.effective_user.username or "NoUsername"
    user_id = str(uuid.uuid1())
    
    # Check if user is already registered
    c.execute("SELECT * FROM brothers WHERE username = ?", (username,))
    existing_user = c.fetchone()
    
    if existing_user:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are already registered!"
        )
    else:
        # Insert new user into the database
        c.execute("INSERT INTO brothers VALUES (?, ?, ?, ?, ?)", 
                  (first_name, surname, username, phone_no, user_id))
        conn.commit()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Registered successfully!"
        )
        

##Accounts profile cmd
async def my_acc(update: Update, context: CallbackContext):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="To use one of the following cmds be in a Private chat with me.Don't request for this or perform this action in a group chats.\n•ONLINE🌐:\n/get_my_profile - get your online account profile.\nNot registered online use /join_online.\n\n•Telegram✈️:\n/get_my_tg_profile - get your telegram profile\n\n/register - not registered? register now.\n\n[v1.00.2 beta]")


##Telegram acc profile cmd
async def get_tg_profile(update: Update, context: CallbackContext):
      
    tg_username = update.effective_user.username
    
    if not tg_username:  
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="You need to set a Telegram username in settings!"
        )
        return  
        
        # Query the database for the user
    c.execute("SELECT * FROM brothers WHERE username = ?", (tg_username,))

    user_info = c.fetchone()
               
    if user_info:
        first_name, surname, username, phone_no, id = user_info  # Unpack the tuple

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Your info/profile:\n"
                 f"Name: {first_name} {surname}\n"
                 f"Username: {username}\n"
                 f"Phone: +{phone_no}\n"
                 f"ID: {id}"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="You need to register first using command /register."
        )
    
    


#Message handling
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    message = update.message.text
    response = ["Hello, how are you?", "Hey there, how is it going?", "Hi friend, hope everything is good?"]
    
    if message == "Hello" or message == "Hey" or message == "hello" or message == "hey":
        await context.bot.send_message(chat_id=update.effective_chat.id, text=random.choice(response))
        
    elif message == "Hola" or message == "Holà" or message == "hola" or message == "holá":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Holà, como estas usted senõr/senõrita")


#Welcoming new members
async def welcome(update: Update, context: CallbackContext):
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result

    # Check if the user joined the chat
    if not was_member and is_member:
        new_member = update.chat_member.new_chat_member.user
        chat = update.effective_chat
        await chat.send_message(f"Welcome, {new_member.mention_html()}, to the Brothers International Community", parse_mode='HTML')

def extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get('status')
    if status_change is None:
        return None

    old_status, new_status = status_change

    was_member = old_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    is_member = new_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]

    return was_member, is_member
    
    

##Def for Job assignment 
async def callback_daily(context: CallbackContext):
    
    await context.bot.send_message(chat_id='@Brotherschatgroup', text='Join the:\n<a href="https://brotherscommmunity.online/">Online community</a>', parse_mode='HTML')


#App setup
TOKEN = "7655042828:AAE6-0juw5pn1wYVUP7aX4xQw36BiYkmBZY"

app = ApplicationBuilder().token(TOKEN).build()


##Assigning job Queue
job_queue = app.job_queue

job_queue.run_daily(callback_daily, time=time(14, 47, 30))


#Registering commands and message handlers
CH = CommandHandler
MH = MessageHandler

#reg. cmds
app.add_handler(CH('start', start))
app.add_handler(CH('help',help))
app.add_handler(CH('join_online', join_online))
app.add_handler(CH('translate', trans_cmd))
app.add_handler(CH('about_us', about_us))
app.add_handler(CH('my_account', my_acc))
app.add_handler(CH('register', register))
app.add_handler(CH('get_my_tg_profile', get_tg_profile))


#reg. msgs
app.add_handler(MH(filters.TEXT & ~filters.COMMAND, handle_messages))
app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))



###I N T E G R A T I O N = with = Next.JS
#. . START

#Next.js project api url
Nextjs_api_url = "https://brothersinternationalcommmunity.online/" 

#profile provider command
async def get_profile(update: Update, context: CallbackContext):
    
    tg_username = update.effective_user.username
    
    if not tg_username:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='You need a Username to perform this action.')
        return 
        
    #fetch the data from next.js api
    response = requests.get(f"{Nextjs_api_url}{tg_username}")
    
    if response.status_code == 200:
        user_data = response.json()
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your profile INFO:\n\nName: {user_data['name']}\nEmail: {user_data['email']}")
    
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Your Username is not found!\nMake sure your username is liked to your account online.')

#. . END
app.add_handler(CH('get_my_profile', get_profile))


#running the bot 
app.run_polling()

