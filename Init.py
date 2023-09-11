import logging
import os
import random
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
        self.urlWordOutput = ""
        self.position = ""
        self.apiPosition = ""
        self.choices = ""
        self.mainButtons = ["Series 📺", "Movies 🎬", "Anime ⛩️", "About ℹ️", "Help 🔍"]
        self.mainKeyboard = [[KeyboardButton(button)] for button in self.mainButtons]
        self.choicesButtons = ["Popular", "Top Rated", "Now Playing", "Upcoming", "Search By Categories",
                               "Search By Name", "Go Back"]
        self.secondKeyBoard = [[KeyboardButton(choice)] for choice in self.choicesButtons]
        self.movieCategories = {'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35, 'Crime': 80,
                                'Documentary': 99, 'Drama': 18, 'Family': 10751, 'Fantasy': 14, 'History': 36,
                                'Horror': 27, 'Music': 10402, 'Mystery': 9648, 'Romance': 10749,
                                'Science Fiction': 878, 'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37,
                                "Done ✅": 0, "Return Back 🔙": 0}
        self.movieCategoriesKeyboard = [[KeyboardButton(button)] for button in self.movieCategories.keys()]
        self.seriesCategories = {'Action & Adventure': 10759, 'Animation': 16, 'Comedy': 35, 'Crime': 80,
                                 'Documentary': 99, 'Drama': 18, 'Family': 10751, 'Kids': 10762, 'Mystery': 9648,
                                 'News': 10763, 'Reality': 10764, 'Sci-Fi & Fantasy': 10765, 'Soap': 10766,
                                 'Talk': 10767, 'War & Politics': 10768, 'Western': 37,
                                 "Done ✅": 0, "Return Back 🔙": 0}
        self.seriesCategoriesKeyboard = [[KeyboardButton(button)] for button in self.seriesCategories.keys()]
        self.names = []
        self.admins = [int(os.getenv("CHATID1")), int(os.getenv("CHATID2"))]
        self.startCommand = CommandHandler("start", self.start)
        self.allCommand = CommandHandler("all", self.all)
        self.countCommand = CommandHandler("count", self.count)
        self.moviesMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Movies)\b', re.IGNORECASE)), self.List)
        self.seriesMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Series)\b', re.IGNORECASE)), self.List)
        self.animeMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:Anime)\b', re.IGNORECASE)), self.anime)
        self.aboutMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:About)\b', re.IGNORECASE)), self.about)
        self.helpMessage = MessageHandler(Filters.regex(re.compile(r'\b(?:help)\b', re.IGNORECASE)), self.help)
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
                MessageHandler(Filters.regex(re.compile(r'(Name)', re.IGNORECASE)),
                               self.searchButton)],
            states={
                self.search: [MessageHandler(Filters.text & ~Filters.command, self.searchInput)],
                self.final: [MessageHandler(Filters.text, self.finalSearchResult)]
            },
            fallbacks=[]
        )
        self.category, self.categorySearchResultMessage = range(2)
        self.categoryValues = ""
        self.categoryMessage = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex(re.compile(r'(Categories)', re.IGNORECASE)), self.categoryList)],
            states={
                self.category: [MessageHandler(Filters.text & ~Filters.command, self.categoryChoices)],
                self.categorySearchResultMessage: [MessageHandler(Filters.text, self.categorySearchResult)]
            },
            fallbacks=[]
        )
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

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

    def error_handler(self, update: Update, context: CallbackContext):
        self.logger.warning(f'Update "{update}" caused error "{context.error}"')
        update.message.reply_text("An error occurred. Please try again later.")

    def List(self, update: Update, context: CallbackContext):
        self.position = update.message.text
        if self.position == self.mainButtons[1]:
            self.apiPosition = "movie"
        elif self.position == self.mainButtons[0]:
            self.apiPosition = "tv"
        self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                              reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))

    def urlWord(self, name):
        self.urlWordOutput = ""
        for c in name:
            if c == ' ':
                self.urlWordOutput += '+'
            elif 65 <= ord(c) <= 90 or 97 <= ord(c) <= 122:
                self.urlWordOutput += c
        return self.urlWordOutput

    def choice(self, update: Update, context: CallbackContext):
        try:
            buttonChoice = update.message.text
            self.choices = buttonChoice
            if self.apiPosition == "tv":
                if buttonChoice == self.choicesButtons[2]:
                    buttonChoice = "Airing Today"
                if buttonChoice == self.choicesButtons[3]:
                    buttonChoice = "On The Air"
            self.data = requests.get(
                f'http://api.themoviedb.org/3/{self.apiPosition}/{buttonChoice.lower().replace(" ", "_")}?api_key={os.getenv("APIKEY")}&page={random.randint(1, 15) if buttonChoice != self.choicesButtons[1] else 1}').json()
            self.names.clear()
            for name in self.data["results"]:
                self.names.append(name['title' if self.apiPosition == 'movie' else 'name'])
            self.names.append("Return Back 🔙")
            keyboardButtons = [[KeyboardButton(name)] for name in self.names]
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text=f"Choose a {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'}:",
                                  reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
            return self.choose
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def choiceMessage(self, update: Update, context: CallbackContext):
        try:
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
                                                                                                                                                                    f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                    f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                        , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                        parse_mode=ParseMode.HTML)
                elif result.status_code == 200:
                    result = result.json()
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text=f"<b>Title</b> 🎬: <b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                               f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                               f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                               f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                   f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                   f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                   f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                   f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                   f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                          , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                          parse_mode=ParseMode.HTML)
                else:
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text="There is a problem right now.\nPlease try again later.",
                                          reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
                return self.choose
            return ConversationHandler.END
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def searchButton(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Enter what you want to search :",
                              reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Return Back 🔙")]],
                                                               resize_keyboard=True))
        return self.search

    def searchInput(self, update: Update, context: CallbackContext):
        try:
            message = update.message.text
            if message == "Return Back 🔙":
                self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                      reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
                return ConversationHandler.END
            self.data = requests.get(
                f'http://api.themoviedb.org/3/search/{self.apiPosition}?query={message}&api_key={os.getenv("APIKEY")}').json()
            self.names.clear()
            if len(self.data["results"]) == 0:
                self.bot.send_message(chat_id=update.message.chat_id,
                                      text=f"The {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'} is not found.",
                                      reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Return Back 🔙")]],
                                                                       resize_keyboard=True))
                return self.search
            for name in self.data["results"]:
                self.names.append(name['title' if self.apiPosition == 'movie' else 'name'])
            self.names.append("Return Back 🔙")
            keyboardButtons = [[KeyboardButton(name)] for name in self.names]
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text=f"Choose a {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'}:",
                                  reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
            return self.final
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def finalSearchResult(self, update: Update, context: CallbackContext):
        try:
            message = update.message.text
            if message == "Return Back 🔙":
                self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                      reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            elif message not in self.names:
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
            else:
                response = requests.get(
                    f"https://image.tmdb.org/t/p/w500{self.data['results'][self.names.index(message)]['poster_path']}")
                result = requests.get(
                    f"https://api.themoviedb.org/3/{self.apiPosition}/{self.data['results'][self.names.index(message)]['id']}?api_key={os.getenv('APIKEY')}")
                if (response.status_code == 200) and (result.status_code == 200):
                    result = result.json()
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_photo(chat_id=update.message.chat_id, photo=response.content,
                                        caption=f"<b>Title</b> 🎬:<b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                                f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                                f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                                f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                    f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                    f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                    f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                    f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                    f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                        , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                        parse_mode=ParseMode.HTML)
                elif result.status_code == 200:
                    result = result.json()
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text=f"<b>Title</b> 🎬: <b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                               f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                               f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                               f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                   f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                   f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                   f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                   f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                   f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                          , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                          parse_mode=ParseMode.HTML)
                else:
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text="There is a problem right now.\nPlease try again later.",
                                          reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
                return self.final
            return ConversationHandler.END
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def categoryList(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="Choose all categories you want from the list\nThen press Done ✅",
                              reply_markup=ReplyKeyboardMarkup(
                                  self.movieCategoriesKeyboard if self.position == self.mainButtons[
                                      1] else self.seriesCategoriesKeyboard, resize_keyboard=True))
        return self.category

    def categoryChoices(self, update: Update, context: CallbackContext):
        try:
            message = update.message.text
            if message == "Return Back 🔙":
                self.categoryValues = ""
                self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                      reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
                return ConversationHandler.END
            elif message == "Done ✅":
                self.data = requests.get(
                    f'http://api.themoviedb.org/3/discover/{self.apiPosition}?api_key={os.getenv("APIKEY")}&sort_by=popularity.desc&page={random.randint(1, 25)}&with_genres={self.categoryValues}').json()
                self.names.clear()
                for name in self.data["results"]:
                    self.names.append(name['title' if self.apiPosition == 'movie' else 'name'])
                self.names.append("Return Back 🔙")
                keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                self.bot.send_message(chat_id=update.message.chat_id,
                                      text=f"Choose a {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'}:",
                                      reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
                return self.categorySearchResultMessage
            else:
                if self.position == self.mainButtons[0]:
                    self.categoryValues += str(self.seriesCategories[message]) if self.categoryValues == "" else " | " + \
                                                                                                                 str(
                                                                                                                     self.seriesCategories[
                                                                                                                         message])
                elif self.position == self.mainButtons[1]:
                    self.categoryValues += str(self.movieCategories[message]) if self.categoryValues == "" else " | " + \
                                                                                                                str(
                                                                                                                    self.movieCategories[
                                                                                                                        message])
            return self.category
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def categorySearchResult(self, update: Update, context: CallbackContext):
        try:
            message = update.message.text
            if message == "Return Back 🔙":
                self.categoryValues = ""
                self.bot.send_message(chat_id=update.message.chat_id, text="Choose from the list:",
                                      reply_markup=ReplyKeyboardMarkup(
                                          self.movieCategoriesKeyboard if self.position == self.mainButtons[
                                              1] else self.seriesCategoriesKeyboard, resize_keyboard=True))
                return self.category
            elif message not in self.names:
                self.bot.send_message(chat_id=update.message.chat_id,
                                      text=f"To search {self.apiPosition.title() if self.apiPosition == 'movie' else 'Serie'} select \"Search By Name\" button.",
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
                                                                                                                                                                    f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                    f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                        , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                        parse_mode=ParseMode.HTML)
                elif result.status_code == 200:
                    result = result.json()
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text=f"<b>Title</b> 🎬: <b>{result['title' if self.apiPosition == 'movie' else 'name']}</b>\n"
                                               f"<b>Category</b> 🎭: {str([result['genres'][i]['name'] for i in range(len(result['genres']))])[1:-1]}\n"
                                               f"<b>{'Duration' if self.apiPosition == 'movie' else 'Seasons'}</b> ⏰: {str(result['runtime'] // 60) + ':' + str(result['runtime'] - ((result['runtime'] // 60) * 60)) if self.apiPosition == 'movie' else result['number_of_seasons']}\n"
                                               f"<b>Rating</b> ⭐️: {float(result['vote_average'])}" + (
                                                   f" <a href='https://www.imdb.com/title/{result['imdb_id']}'>imdb</a>" if self.apiPosition == 'movie' else "") + "\n"
                                                                                                                                                                   f"<b>Release date</b> 📅: {result['release_date' if self.apiPosition == 'movie' else 'first_air_date']}\n"
                                                                                                                                                                   f"<b>Language</b> 🎤: {result['original_language']}\n"
                                                                                                                                                                   f"<b>Overview</b> ℹ️: {result['overview'][:250] + ' ...' if len(result['overview']) != 0 else 'N/A'}\n"
                                                                                                                                                                   f"<b>Watch it from</b> : <a href='https://ww2.123moviesfree.net/search/?q={self.urlWord(message)}'>Here</a>"
                                          , reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True),
                                          parse_mode=ParseMode.HTML)
                else:
                    keyboardButtons = [[KeyboardButton(name)] for name in self.names]
                    self.bot.send_message(chat_id=update.message.chat_id,
                                          text="There is a problem right now.\nPlease try again later.",
                                          reply_markup=ReplyKeyboardMarkup(keyboardButtons, resize_keyboard=True))
                return self.categorySearchResultMessage
            return ConversationHandler.END
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id=update.message.chat_id,
                                  text="There is a problem.\nPlease try again after restarting /start",
                                  reply_markup=ReplyKeyboardMarkup(self.secondKeyBoard, resize_keyboard=True))
            return ConversationHandler.END

    def anime(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id, text="Coming Soon ...",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))

    def about(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="This bot will helps you to find the suitable show for you.\nBot developers:\n@obadaalkatma , @MohammadAl55",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))

    def help(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="If the bot is not working just restart it using /start .\nYou can contact bot developers if there is any problem.",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True), )

    def all(self, update: Update, context: CallbackContext):
        message = update.message.text[5:]
        if message == "" and update.message.chat_id == int(os.getenv("CHATID")):
            self.bot.send_message(chat_id=int(os.getenv("CHATID")), text="The message is empty.\nPlease resend it.")
        elif update.message.chat_id != int(os.getenv("CHATID")):
            self.bot.send_message(chat_id=update.message.chat_id, text="Only bot admins can use this command")
        else:
            if update.message.chat_id == int(os.getenv("CHATID")):
                with open("id.txt", "r") as file:
                    for id in file:
                        try:
                            self.bot.send_message(chat_id=int(id[:-1]), text=message)
                        except Exception as e:
                            print(e)

    def count(self, update: Update, context: CallbackContext):
        chatId = update.message.chat_id
        if chatId in self.admins:
            data = open("id.txt", "r")
            self.bot.send_message(chat_id=chatId,
                                  text=f"The number of bot users id : {len(data.readlines())}")
            data.close()
        else:
            self.bot.send_message(chat_id=update.message.chat_id, text="Only bot admins can use use this command.")

    def goBack(self, update: Update, context: CallbackContext):
        self.bot.send_message(chat_id=update.message.chat_id,
                              text="Choose what you want:",
                              reply_markup=ReplyKeyboardMarkup(self.mainKeyboard, resize_keyboard=True))
        return ConversationHandler.END
