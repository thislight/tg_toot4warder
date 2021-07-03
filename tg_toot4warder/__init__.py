import logging
from dataclasses import dataclass
import time
from typing import Any, Dict, Iterator, Optional, Union

import arrow
import httpx
from bs4 import BeautifulSoup
from httpx import Client
from telegram.chat import Chat
from telegram.ext import Updater
from telegram.ext.callbackcontext import CallbackContext

from . import remote_measurement


_logger = logging.getLogger("tg_toot4warder")


class MastodonUser(object):
    def __init__(
        self,
        mastodon_base_uri: str,
        mastodon_id: str,
        remote_measurement_records_n: int,
    ) -> None:
        self.mastodon_id = mastodon_id
        self.api_http_client = Client(
            base_url="{}/api/".format(mastodon_base_uri), timeout=10
        )
        self.remote_measurement = remote_measurement.RemoteMeasurement(
            remote_measurement_records_n
        )
        super().__init__()


@dataclass
class Account(object):
    id: str
    acct: str
    display_name: str


@dataclass
class Toot(object):
    id: str
    created_at: arrow.Arrow
    content: str
    url: str
    account: Account
    reblog: Optional["Toot"] = None


def parse_account(el: Dict[str, Any]) -> Account:
    return Account(id=el["id"], acct=el["acct"], display_name=el["display_name"])


def parse_toot(el: Dict[str, Any]) -> Toot:
    return Toot(
        id=el["id"],
        created_at=arrow.get(el["created_at"]),
        content=el["content"],
        url=el["url"],
        account=parse_account(el["account"]),
        reblog=parse_toot(el["reblog"]) if el.get("reblog", None) else None,
    )


class MastodonRemoteUnavailable(Exception):
    def __init__(self, remote: str, error_type: str) -> None:
        self.remote = remote
        self.error_type = error_type
        super().__init__(remote, "service unavaliable")


def _push_failing_measurement_data(
    user: MastodonUser, requesting_time: arrow.Arrow, t1: float
):
    remote_measurement.push_data(
        user.remote_measurement,
        remote_measurement.MeasurementData(
            time=requesting_time,
            responded=False,
            success=False,
            time_cost=time.perf_counter() - t1,
        ),
    )


def _get_latest_toots(user: MastodonUser) -> Iterator[Toot]:
    requesting_time = arrow.get()
    try:
        t1 = time.perf_counter()
        statuses_http_response = user.api_http_client.get(
            "v1/accounts/{}/statuses".format(user.mastodon_id)
        )
        statuses_http_response.raise_for_status()
    except httpx.TimeoutException as e:
        _push_failing_measurement_data(user, requesting_time, t1)
        raise MastodonRemoteUnavailable(
            str(user.api_http_client.base_url), "timeout"
        ) from e
    except httpx.NetworkError as e:
        _push_failing_measurement_data(user, requesting_time, t1)
        raise MastodonRemoteUnavailable(
            str(user.api_http_client.base_url), "network"
        ) from e
    except httpx.HTTPStatusError as e:
        _push_failing_measurement_data(user, requesting_time, t1)
        raise MastodonRemoteUnavailable(
            str(user.api_http_client.base_url), "http_status"
        ) from e
    statuses_response: list[dict[str, Any]] = statuses_http_response.json()
    try:
        assert isinstance(statuses_response, list)
    except AssertionError as e:
        remote_measurement.push_data(
            user.remote_measurement,
            remote_measurement.MeasurementData(
                time=requesting_time,
                responded=True,
                success=False,
                time_cost=time.perf_counter() - t1,
            ),
        )
        raise e
    remote_measurement.push_data(
        user.remote_measurement,
        remote_measurement.MeasurementData(
            time=requesting_time,
            responded=True,
            success=True,
            time_cost=time.perf_counter() - t1,
        ),
    )
    for el in statuses_response:
        yield parse_toot(el)


def get_latest_toots(user: MastodonUser, *, retries: int = 3) -> Iterator[Toot]:
    tries = retries + 1
    for current_try in range(tries):
        try:
            return _get_latest_toots(user)
        except MastodonRemoteUnavailable as e:
            _logger.info(
                "_get_latest_toots() failed. Retry now: the {} of {} tries.".format(
                    current_try, tries
                )
            )
            if current_try == retries:
                raise e
    raise RuntimeError("Dont reach here")


class TootForwarderBot(object):
    def __init__(
        self,
        tg_bot_token: str,
        target_chat_identifier: Union[int, str],
        mastodon_user: MastodonUser,
        *,
        disable_notification: bool = True,
        toots_polling_interval: int = 60,  # in seconds
    ) -> None:
        self.tg_bot_token = tg_bot_token
        self.target_chat_identifier = target_chat_identifier
        self.mastodon_user = mastodon_user
        self.last_checked_time = arrow.utcnow()
        self.mastodon_remote_available = False
        self.disable_notification = disable_notification
        self.toots_polling_interval = toots_polling_interval
        super().__init__()


def exact_all_text_from_html(s: str):
    soup = BeautifulSoup(s, "html.parser")
    return soup.get_text(separator='\n')


def _send_mastodon_remote_error_notification(
    target_chat: Chat, e: MastodonRemoteUnavailable, disable_notification: bool
):
    BASE_MESSAGE = "Could not contract {remote}.\n\n{reason}"
    if e.error_type == "timeout":
        message = BASE_MESSAGE.format(
            remote=e.remote, reason="Timeout while contracting."
        )
    elif e.error_type == "network":
        message = BASE_MESSAGE.format(remote=e.remote, reason="Network problem.")
    elif e.error_type == "http_status":
        message = BASE_MESSAGE.format(
            remote=e.remote, reason="Unexecpted result status."
        )
    else:
        message = BASE_MESSAGE.format(remote=e.remote, reason="Unknown error.")
        raise RuntimeError("Unsupported error")
    target_chat.send_message(message, disable_notification=disable_notification)


def forward_toot(target_chat: Chat, toot: Toot, *, disable_notification: bool = False):
    TEMPLATE_NOREBLOG = "{content}\n\n{link}"
    TEMPLATE_REBLOG = "{content}\n\nRetooted from {original_user_display_name}.\n{link}"
    toot_text_content = exact_all_text_from_html(toot.content)
    if toot.reblog:
        text_message = TEMPLATE_REBLOG.format(
            content=toot_text_content,
            link=toot.reblog.url,
            original_user_display_name=toot.reblog.account.display_name,
        )
    else:
        text_message = TEMPLATE_NOREBLOG.format(
            content=toot_text_content,
            link=toot.url,
        )
    target_chat.send_message(
        text_message,
        disable_notification=disable_notification,
    )


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
        try:
            toots_iter = get_latest_toots(bot.mastodon_user)
            for toot in toots_iter:
                total += 1
                logging.debug("Processing toot: %s", toot)
                if toot.created_at > bot.last_checked_time:
                    _logger.info("Forwarding %s.", toot)
                    forwarded += 1
                    forward_toot(
                        target_chat, toot, disable_notification=bot.disable_notification
                    )
                    bot.last_checked_time = toot.created_at
                else:
                    skipped += 1
            bot.mastodon_remote_available = True
        except MastodonRemoteUnavailable as e:
            if (
                remote_measurement.total_success_possibility(bot.mastodon_user.remote_measurement) < 0.5
            ) and (not bot.mastodon_remote_available):
                _send_mastodon_remote_error_notification(
                    target_chat, e, disable_notification=bot.disable_notification
                )
            bot.mastodon_remote_available = False
            _logger.error(
                "Mastodon remote %s is unavailable? Responded %s%% (success %s%%) in %s to %s (as %s)",
                e.remote,
                remote_measurement.total_responded_possibility(
                    bot.mastodon_user.remote_measurement
                ),
                remote_measurement.total_success_possibility(bot.mastodon_user.remote_measurement),
                remote_measurement.time_range_start(bot.mastodon_user.remote_measurement),
                remote_measurement.time_range_end(bot.mastodon_user.remote_measurement),
                remote_measurement.time_delta(bot.mastodon_user.remote_measurement),
                exc_info=e,
            )
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
        bot.toots_polling_interval,
    )

    return updater
