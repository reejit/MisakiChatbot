from time import time
from pyrogram import filters

from coffeehouse.lydia import LydiaAI
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError

from chatbot import app, LOGGER, CF_API_KEY, NAME
import chatbot.bot.database.chatbot_db as db


CoffeeHouseAPI = API(CF_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


HELP_TEXT = """ • Reply `/adduser` to yourself to enable the chatbot for your ID!\n• Reply `/rmuser` to yourself to stop the chatbot for your ID! \nHave fun!"""

@app.on_message(filters.command("start"))
def start(client, message):
    pic = "https://telegra.ph/file/f4a32d686bee0746183bb.jpg"
    message.reply_photo(pic, caption="Misaki - v0.1\n Using Coffeehouse AI from @Intellivoid\n Do `/help` to know more :D")


@app.on_message(filters.command("help"))
def help(client, message):
    message.reply_text(HELP_TEXT, parse_mode="md")
    

@app.on_message(filters.command("adduser"))
def add_user(client, message):
    if not message.reply_to_message:
        message.reply_text("Reply to someone to enable chatbot for that person!")
        return
    user_id = message.reply_to_message.from_user.id
    is_user = db.is_user(user_id)
    if not is_user:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        db.set_ses(user_id, ses_id, expires)
        message.reply_text("AI enabled for user successfully!")
        LOGGER.info(f"AI enabled for user - {user_id}")
    else:
        message.reply_text("AI is already enabled for this user!")
        

@app.on_message(filters.command("rmuser"))
def rem_user(client, message):
    if not message.reply_to_message:
        message.reply_text("You've gotta reply to someone!")
        return
    user_id = message.reply_to_message.from_user.id
    is_user = db.is_user(user_id)
    if not is_user:
        message.reply_text("AI isn't enabled for this user in the first place!")
    else:
        db.rem_user(user_id)
        message.reply_text("AI disabled for this user successfully!")
        LOGGER.info(f"AI disabled for user - {user_id}")


def check_message(client, msg):
    reply_msg = msg.reply_to_message
    if NAME.lower() in msg.text.lower():
        return True
    if reply_msg and reply_msg.from_user is not None:
        if reply_msg.from_user.is_self:
            return True
    return False
    
        
@app.on_message(filters.text)
def chatbot(client, message):
    msg = message
    if not check_message(client, msg):
        return
    user_id = msg.from_user.id
    if not user_id in db.USERS:
        return
    sesh, exp = db.get_ses(user_id)
    query = msg.text
    if int(exp) < time():
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        db.set_ses(user_id, ses_id, expires)
        sesh, exp = ses_id, expires
        
    try:
        app.send_chat_action(msg.chat.id, "typing")
        response = api_client.think_thought(sesh, query)
        msg.reply_text(response)
    except CFError as e:
        app.send_message(chat_id=msg.chat.id, text=f"An error occurred:\n`{e}`", parse_mode="md")
