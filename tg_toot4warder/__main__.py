import asyncio
from email.policy import default
from functools import wraps
import os
import sys
from typing import Union
import click
from tg_toot4warder import create_updater, MastodonUser, TootForwarderBot
import aiogram

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
    help='Identifier for the chat, may be the username (with prefix "@") or a integer. (accept environment variable TARGET_CHAT_ID)',
    envvar="TARGET_CHAT_ID",
)
@click.option(
    "--verbose/--no-verbose",
    "verbose",
    help="Output more verbose debugging message.",
    type=bool,
    default=False,
)
@click.option(
    "--disable-notification/--enable-notification",
    "disable_notification",
    help="Turn off the notification for messages. (accept environment variable DISABLE_NOTIFICATION)",
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
@click.option(
    "--min-success-rate",
    "min_success_rate",
    type=float,
    help="Send a notification message to target channel when success rate is less than this value, the default is 0.5. Should be >=0, <=1.",
    envvar="MIN_SUCCESS_RATE",
    default=0.5,
)
@click.option(
    "--dryrun/--disable-dryrun",
    "dryrun",
    type=bool,
    help="Don't send any message to the telegram chat.",
    default=False,
)
@click.option(
    "--mock-toots/--no-mock-toots",
    "mock_toots",
    type=bool,
    help="Use fake toots instead of fetching from remote, should be used with --dryrun option",
    default=False,
)
def toot4warder(
    mastodon_instance: str,
    mastodon_id: int,
    tg_bot_token: str,
    target_chat_id: str,
    verbose: bool,
    disable_notification: bool,
    toots_polling_interval: int,
    min_success_rate: float,
    dryrun: bool,
    mock_toots: bool,
):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
        stream=sys.stderr,
    )
    if not target_chat_id.startswith("@"):
        real_target_chat_id: Union[str, int] = int(target_chat_id)
    else:
        real_target_chat_id = target_chat_id
    user = MastodonUser(
        mastodon_instance,
        str(mastodon_id),
        60,
        mock_toots,
    )
    bot = TootForwarderBot(
        tg_bot_token,
        real_target_chat_id,
        user,
        disable_notification=disable_notification,
        toots_polling_interval=toots_polling_interval,
        min_success_rate=min_success_rate,
        dryrun=dryrun,
    )
    assert (not mock_toots) or (
        dryrun and mock_toots
    ), "--mock-toots should be used with --dryrun"
    loop = asyncio.get_event_loop()
    updater = loop.run_until_complete(create_updater(bot))
    aiogram.executor.start_polling(updater)


def main():
    toot4warder()


if __name__ == "__main__":
    main()
