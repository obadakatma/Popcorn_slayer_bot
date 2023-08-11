import os
from Init import Init

TOKEN = os.getenv("TOKEN")
init = Init(TOKEN)
dp = init.update.dispatcher
dp.add_handler(init.startCommand)
dp.add_handler(init.messageCommand)
init.update.start_polling()
init.update.idle()