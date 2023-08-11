import os

import requests
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import telegram


class Init:
    def __init__(self, TOKEN):
        self.update = Updater(token=TOKEN)
        self.bot = telegram.Bot(token=TOKEN)
        self.startCommand = CommandHandler("start", self.start)
        self.messageCommand = MessageHandler(filters=Filters.text, callback=self.message)

    def start(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text=f"Hi {update.message.chat.full_name}\nWelcome to Popcon Slayer Bot")
        found = False
        userid = update.message.chat_id
        with open("id.txt", "r") as Id:
            if str(userid) in Id.read():
                found = True
            Id.close()
        with open("id.txt", "a") as Id:
            if not found:
                Id.write(f"{userid}\n")
            Id.close()

    def message(self, update: Update, context: CallbackContext):
        message = update.message.text
        apikey = os.getenv("APIKEY")
        data = requests.get(
            f'http://api.themoviedb.org/3/search/movie?api_key={apikey}&query={message}').json()
        self.bot.send_photo(chat_id=update.message.chat_id,
                            photo=f'https://image.tmdb.org/t/p/w500{data["results"][0]["poster_path"]}')
        self.bot.send_message(chat_id=update.message.chat_id, text=f'Movie Name: {data["results"][0]["title"]}\n'
                                                                   f'Release Date: {data["results"][0]["release_date"]}\n'
                                                                   f'Rating: {data["results"][0]["vote_average"]}')
