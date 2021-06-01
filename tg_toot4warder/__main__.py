import os
import click
from tg_toot4warder import create_updater, MastodonUser, TootForwarderBot

import logging


@click.command()
@click.option(
    "--instance",
    "mastodon_instance",
    required=True,
    help="Mastodon instance address. (accept environment variable MASTODON_INSTANCE)",
    default="https://mastodon.social",
    type=str,
    envvar="MASTODON_INSTANCE",
)
@click.option(
    "--id",
    "mastodon_id",
    required=True,
    help="Your unique integer on the instance. (accept environment variable MASTODON_ID)",
    type=int,
    envvar="MASTODON_ID",
)
@click.option(
    "--bot-token",
    "tg_bot_token",
    required=True,
    help="Access token for telegram bot. (accept environment variable BOT_TOKEN)",
    type=str,
    envvar="BOT_TOKEN",
)
@click.option(
    "--target-chat",
    "target_chat_id",
    required=True,
    help='Identifier for the chat, may be the username (with prefix "@") or integer. (accept environment variable TARGET_CHAT_ID)',
    envvar="TARGET_CHAT_ID",
)
@click.option(
    '--verbose/--no-verbose',
    'verbose',
    help="Print out more verbose debugging message.",
    type=bool,
    default=False,
)
def toot4warder(mastodon_instance, mastodon_id, tg_bot_token, target_chat_id, verbose: bool):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )
    user = MastodonUser(
        mastodon_instance,
        mastodon_id,
    )
    bot = TootForwarderBot(
        tg_bot_token,
        target_chat_id,
        user,
    )
    updater = create_updater(bot)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    toot4warder()
