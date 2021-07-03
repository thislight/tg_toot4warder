import os
from typing import Union
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
    "--verbose/--no-verbose",
    "verbose",
    help="Print out more verbose debugging message.",
    type=bool,
    default=False,
)
@click.option(
    "--disable-notification/--enable-notification",
    "disable_notification",
    help="Should the telegram message have notification. (accept environment variable DISABLE_NOTIFICATION)",
    type=bool,
    default=True,
    envvar="DISABLE_NOTIFICATION",
)
@click.option(
    "--toots-polling-interval",
    "toots_polling_interval",
    type=int,
    help="The polling interval in seconds for toots, the default is 60. (accept environment variable TOOTS_POLLING_INTERVAL)",
    envvar="TOOTS_POLLING_INTERVAL",
    default=60,
)
def toot4warder(
    mastodon_instance: str,
    mastodon_id: int,
    tg_bot_token: str,
    target_chat_id: str,
    verbose: bool,
    disable_notification: bool,
    toots_polling_interval: int,
):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )
    if not target_chat_id.startswith('@'):
        real_target_chat_id: Union[str, int] = int(target_chat_id)
    else:
        real_target_chat_id = target_chat_id
    user = MastodonUser(
        mastodon_instance,
        str(mastodon_id),
        60,
    )
    bot = TootForwarderBot(
        tg_bot_token,
        real_target_chat_id,
        user,
        disable_notification=disable_notification,
        toots_polling_interval=toots_polling_interval,
    )
    updater = create_updater(bot)
    updater.start_polling()
    updater.idle()


def main():
    toot4warder()


if __name__ == "__main__":
    main()
