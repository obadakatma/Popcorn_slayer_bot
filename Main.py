import os
from Init import Init

TOKEN = os.getenv("TOKEN")
init = Init(TOKEN)
dp = init.update.dispatcher
dp.add_handler(init.startCommand)
dp.add_handler(init.choiceMessage)
dp.add_handler(init.moviesMessage)
dp.add_handler(init.seriesMessage)
dp.add_handler(init.animeMessage)
dp.add_handler(init.aboutMessage)
dp.add_handler(init.goBackButton)
init.update.start_polling()
init.update.idle()
