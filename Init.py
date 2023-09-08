import os
import re

import requests
import telegram
from telegram import ParseMode
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.keyboardbutton import KeyboardButton
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from telegram.update import Update


class Init:
    def __init__(self, TOKEN):
        self.update = Updater(token=TOKEN)
        self.bot = telegram.Bot(token=TOKEN)
        self.data = None
        self.position = ""
        self.apiPosition = ""
        self.choices = ""
        self.mainButtons = ["Series 📺", "Movies 🎬", "Anime ⛩️", "About ℹ️"]
        self.mainKeyboard = [[KeyboardButton(button)] for button in self.mainButtons]
        self.choicesButtons = ["Popular", "Top Rated", "Now Playing", "Upcoming", "Search", "Go Back"]
        self.secondKeyBoard = [[KeyboardButton(choise)] for choise in self.choicesButtons]
        self.names = []
        self.startCommand = CommandHandler("start", self.start)
        self.moviesMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Movies)\b', re.IGNORECASE)), self.List)
        self.seriesMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Series)\b', re.IGNORECASE)), self.List)
        self.animeMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Anime)\b', re.IGNORECASE)), self.anime)
        self.aboutMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:About)\b', re.IGNORECASE)), self.about)
        self.goBackMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Go Back)\b', re.IGNORECASE)),
                                            self.goBack)
        self.choose = range(1)
        self.choiceMessage = ConversationHandler(
            entry_points=[
                MessageHandler(
                    Filters.regex(re.compile(r'(Popular|Top Rated|Now Playing|Upcoming)', re.IGNORECASE)),
                    self.choice)],
            states={
                self.choose: [MessageHandler(Filters.text, self.choiceMessage)]
            },
            fallbacks=[]
        )
        self.search, self.final = range(2)
        self.searchMessage = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.regex(re.compile(r'(Search)', re.IGNORECASE)),
                               self.searchButton)],
            states={
                self.search: [MessageHandler(Filters.text & ~Filters.command, self.searchInput)],
                self.final: [MessageHandler(Filters.text, self.finalSearchResult)]
            },
            fallbacks=[]
        )

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

    def List(self, update: Update, context: CallbackContext):
        self.position = update.message.text
        if self.position == self.mainButtons[1]:
            self.apiPosition = "movie"
        elif self.position == self.mainButtons[0]:
            self.apiPosition = "tv"
        self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                              reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))

    def choice(self, update: Update, context: CallbackContext):
        buttonChoice = update.message.text
        self.choices = buttonChoice
        if self.apiPosition == "tv":
            if buttonChoice == self.choicesButtons[2]:
                buttonChoice = "Airing Today"
            if buttonChoice == self.choicesButtons[3]:
                buttonChoice = "On The Air"
        self.data = requests.get(
            f'http://api.themoviedb.org/3/{self.apiPosition}/{buttonChoice.lower().replace(" ", "_")}?api_key={os.getenv("APIKEY")}').json()
        self.names.clear()
        for name in self.data["results"]:
            self.names.append(name['title' if self.apiPosition == 'movie' else 'name'])
        self.names.append("Return Back 🔙")
        keyboardButtons = [[KeyboardButton(name)] for name in self.names]
        self.bot.send_message(chat_id=update.message.chat_id,
                              text=f"Choose a {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'}:",
                              reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
        return self.choose

    def choiceMessage(self, update: Update, context: CallbackContext):
        message = update.message.text
        if message == "Return Back 🔙":
            self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
        elif message not in self.names:
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text=f"{self.position[:-1].title()}name not in the {self.choices.title()} list\nChoose from the list:",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
        elif message in self.names:
            response = requests.get(
                f"https://image.tmdb.org/t/p/w500{self.data['results'][self.names.index(message)]['poster_path']}")
            result = requests.get(
                f"https://api.themoviedb.org/3/{self.apiPosition}/{self.data['results'][self.names.index(message)]['id']}?api_key={os.getenv('APIKEY')}")
            if (response.status_code == 200) and (result.status_code == 200):
                result = result.json()
                keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                self.bot.send_photo(chat_id=update.message.chat_id, photo=response.content,
                                    caption=f"<b>Title</b> 🎬: <b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                            f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                            f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                            f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                f"<b>Overview</b> ℹ️: {result['overview'][:result['overview'].index('.') + 1] if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={message}'>Here</a>"
                                    , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                    parse_mode=ParseMode.HTML)
            return self.choose
        return ConversationHandler.END

    def searchButton(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Enter what you want to search :",
                              reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Return Back 🔙")]],
                                                               resize_keyboard=True))
        return self.search

    def searchInput(self, update: Update, context: CallbackContext):
        message = update.message.text
        if message == "Return Back 🔙":
            self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END
        self.data = requests.get(
            f'http://api.themoviedb.org/3/search/{self.apiPosition}?query={message}&api_key={os.getenv("APIKEY")}').json()
        self.names.clear()
        for name in self.data["results"]:
            self.names.append(name['title' if self.apiPosition == 'movie' else 'name'])
        self.names.append("Return Back 🔙")
        keyboardButtons = [[KeyboardButton(name)] for name in self.names]
        self.bot.send_message(chat_id=update.message.chat_id,
                              text=f"Choose a {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'}:",
                              reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
        return self.final

    def finalSearchResult(self, update: Update, context: CallbackContext):
        message = update.message.text
        if message == "Return Back 🔙":
            self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
        else:
            response = requests.get(
                f"https://image.tmdb.org/t/p/w500{self.data['results'][self.names.index(message)]['poster_path']}")
            result = requests.get(
                f"https://api.themoviedb.org/3/{self.apiPosition}/{self.data['results'][self.names.index(message)]['id']}?api_key={os.getenv('APIKEY')}")
            if (response.status_code == 200) and (result.status_code == 200):
                result = result.json()
                keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                self.bot.send_photo(chat_id=update.message.chat_id, photo=response.content,
                                    caption=f"<b>Title</b> 🎬: <b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                            f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                            f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                            f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                f"<b>Overview</b> ℹ️: {result['overview'] if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={message}'>Here</a>"
                                    , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                    parse_mode=ParseMode.HTML)
            return self.final
        return ConversationHandler.END

    def anime(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Coming Soon",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))

    def about(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="This bot will helps you to find the suitable show for you.\nBot developers:\n@obadaalkatma , @MohammadAl55",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))

    def goBack(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="Choose what you want:",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))
        return ConversationHandler.END
