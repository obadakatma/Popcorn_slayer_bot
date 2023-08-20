import os
import re

import requests
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.keyboardbutton import KeyboardButton
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
import telegram


class Init:
    def __init__(self, TOKEN):
        self.update = Updater(token=TOKEN)
        self.bot = telegram.Bot(token=TOKEN)
        self.mainButtons = ["Series📺", "Movies🎬"]
        self.mainKeyboard = [[KeyboardButton(button)] for button in self.mainButtons]
        self.secondButtons = ["Popular", "Top Rated", "Now Playing", "Upcoming", "Categories", "Search", "Go Back"]
        self.secondKeyBoard = [[KeyboardButton(choise)] for choise in self.secondButtons]
        self.startCommand = CommandHandler("start", self.start)
        self.movieConversation = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex(re.compile(r'\b(?:Movies)\b', re.IGNORECASE)), self.movieList)],
            states={

            },
            fallbacks=[]
        )
        self.seriesConversation = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex(re.compile(r'\b(?:Series)\b', re.IGNORECASE)), self.seriesList)],
            states={

            },
            fallbacks=[]
        )
        self.goBackButton = MessageHandler(Filters.regex(re.compile(r'\b(?:Go Back)\b', re.IGNORECASE)),
                                           self.goBackMessage)

    def start(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text=f"Hi {update.message.chat.full_name}\nWelcome to Popcon Slayer Bot",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))
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

    def movieList(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                              reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard))

    def seriesList(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                              reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard))

    def goBackMessage(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="Choose what you want:",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))
        return ConversationHandler.END
