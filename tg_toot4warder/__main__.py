import os
from tg_toot4warder import create_updater, MastodonUser, TootForwarderBot

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

user = MastodonUser(
    os.environ['MASTODON_INSTANCE'],
    os.environ['MASTODON_ID'],
)

bot = TootForwarderBot(
    os.environ['BOT_TOKEN'],
    os.environ['TARGET_CHAT_ID'],
    user,
)

updater = create_updater(bot)

updater.start_polling()

updater.idle()
