import os
from dotenv import load_dotenv
from Init import Init

load_dotenv()

TOKEN = os.getenv("TOKEN")
init = Init(TOKEN)
dp = init.update.dispatcher
dp.add_handler(init.startCommand)
dp.add_handler(init.allCommand)
dp.add_handler(init.countCommand)
dp.add_handler(init.choiceMessage)
dp.add_handler(init.searchMessage)
dp.add_handler(init.categoryMessage)
dp.add_handler(init.moviesMessage)
dp.add_handler(init.seriesMessage)
dp.add_handler(init.animeMessage)
dp.add_handler(init.aboutMessage)
dp.add_handler(init.helpMessage)
dp.add_handler(init.goBackMessage)

init.update.start_polling()
init.update.idle()