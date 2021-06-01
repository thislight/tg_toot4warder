import logging
from dataclasses import dataclass
from os import link
from typing import Any, Iterator, Union

import arrow
import dateutil.parser
from bs4 import BeautifulSoup
from httpx import Client
from telegram.chat import Chat
from telegram.ext import Updater
from telegram.ext.callbackcontext import CallbackContext

A_MINUTE = 60

_logger = logging.getLogger("tg_toot4warder")


class MastodonUser(object):
    def __init__(self, mastodon_base_uri: str, mastodon_id: str) -> None:
        self.mastodon_id = mastodon_id
        self.api_http_client = Client(base_url=f"{mastodon_base_uri}/api/", timeout=10)
        super().__init__()


@dataclass
class Toot(object):
    id: str
    created_at: arrow.Arrow
    content: str
    url: str


def get_latest_toots(user: MastodonUser) -> Iterator[Toot]:
    statuses_http_response = user.api_http_client.get(
        f"v1/accounts/{user.mastodon_id}/statuses"
    )
    statuses_response: list[dict[str, Any]] = statuses_http_response.json()
    assert isinstance(statuses_response, list)
    for el in statuses_response:
        yield Toot(
            id=el["id"],
            created_at=arrow.get(el['created_at']),
            content=el["content"],
            url=el["url"],
        )


class TootForwarderBot(object):
    def __init__(
        self,
        tg_bot_token: str,
        target_chat_identifier: Union[int, str],
        mastodon_user: MastodonUser,
    ) -> None:
        self.tg_bot_token = tg_bot_token
        self.target_chat_identifier = target_chat_identifier
        self.mastodon_user = mastodon_user
        self.last_checked_time = arrow.utcnow()
        super().__init__()


def exact_all_text_from_html(s: str):
    soup = BeautifulSoup(s, "html.parser")
    return soup.get_text()


def _make_checking_and_forwarding_job_callback(
    bot: TootForwarderBot, target_chat: Chat
):
    def _checking_and_forwarding_job(ctx: CallbackContext):
        _logger.info(
            "Checking new toots. Last checked time: {}.".format(
                repr(bot.last_checked_time)
            )
        )
        total, forwarded, skipped = 0, 0, 0
        for toot in get_latest_toots(bot.mastodon_user):
            total += 1
            logging.debug("Processing toot: %s", toot)
            if toot.created_at > bot.last_checked_time:
                _logger.info("Forwarding %s.", toot)
                forwarded += 1
                target_chat.send_message(
                    "{content}\n\n{link}".format(
                        content=exact_all_text_from_html(toot.content), link=toot.url
                    ),
                    disable_notification=True,
                )
                bot.last_checked_time = toot.created_at
            else:
                skipped += 1
        _logger.info(
            "Done! Total/Forwarded/Skipped: {}/{}/{}.".format(total, forwarded, skipped)
        )

    return _checking_and_forwarding_job


def create_updater(bot: TootForwarderBot) -> Updater:
    updater = Updater(bot.tg_bot_token)

    _logger.info("Getting chat of '{}'.".format(bot.target_chat_identifier))
    target_chat = updater.bot.get_chat(bot.target_chat_identifier)
    assert target_chat, "Could not get the target channel"

    job_queue = updater.job_queue
    job_queue.run_repeating(
        _make_checking_and_forwarding_job_callback(bot, target_chat),
        A_MINUTE,
    )

    return updater
