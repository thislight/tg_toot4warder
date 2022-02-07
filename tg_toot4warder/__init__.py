import asyncio
import json
import logging
from dataclasses import dataclass
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

import arrow
import httpx
from bs4 import BeautifulSoup
from httpx import AsyncClient

from . import remote_measurement
import aiogram

_logger = logging.getLogger("tg_toot4warder")

FAKE_TOOTS_DATA = json.loads(
    r"""[{"id":"107755621835790856","created_at":"2022-02-07T07:51:43.901Z","in_reply_to_id":null,"in_reply_to_account_id":null,"sensitive":false,"spoiler_text":"","visibility":"public","language":"zh-CN","uri":"https://mastodon.social/users/thislight/statuses/107755621835790856","url":"https://mastodon.social/@thislight/107755621835790856","replies_count":0,"reblogs_count":0,"favourites_count":0,"edited_at":null,"favourited":false,"reblogged":false,"muted":false,"bookmarked":false,"pinned":false,"content":"<p>Orz又又又又要住院了……</p>","reblog":null,"application":{"name":"Mastodon for iOS","website":"https://app.joinmastodon.org/ios"},"account":{"id":"150831","username":"thislight","acct":"thislight","display_name":"thislight","locked":false,"bot":false,"discoverable":true,"group":false,"created_at":"2017-05-29T00:00:00.000Z","note":"<p>Developer, Designer.</p>","url":"https://mastodon.social/@thislight","avatar":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","avatar_static":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","header":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","header_static":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","followers_count":17,"following_count":21,"statuses_count":729,"last_status_at":"2022-02-07","emojis":[],"fields":[{"name":"GitHub","value":"<a href=\"https://github.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">github.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"GitLab","value":"<a href=\"https://gitlab.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">gitlab.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"Blog","value":"<a href=\"https://rubicon.lightstands.xyz\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">rubicon.lightstands.xyz</span><span class=\"invisible\"></span></a>","verified_at":"2020-12-27T15:23:23.054+00:00"},{"name":"Donate (liberapay)","value":"<a href=\"https://liberapay.com/thisLight/donate\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">liberapay.com/thisLight/donate</span><span class=\"invisible\"></span></a>","verified_at":"2021-03-11T00:51:51.566+00:00"}]},"media_attachments":[],"mentions":[],"tags":[],"emojis":[],"card":null,"poll":null},{"id":"107751441476337212","created_at":"2022-02-06T14:08:36.668Z","in_reply_to_id":null,"in_reply_to_account_id":null,"sensitive":false,"spoiler_text":"","visibility":"public","language":"zh","uri":"https://mastodon.social/users/thislight/statuses/107751441476337212","url":"https://mastodon.social/@thislight/107751441476337212","replies_count":0,"reblogs_count":0,"favourites_count":0,"edited_at":null,"favourited":false,"reblogged":false,"muted":false,"bookmarked":false,"pinned":false,"content":"<p>简单触发一个编译器bug……</p>","reblog":null,"application":{"name":"Tootle","website":"https://github.com/bleakgrey/tootle"},"account":{"id":"150831","username":"thislight","acct":"thislight","display_name":"thislight","locked":false,"bot":false,"discoverable":true,"group":false,"created_at":"2017-05-29T00:00:00.000Z","note":"<p>Developer, Designer.</p>","url":"https://mastodon.social/@thislight","avatar":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","avatar_static":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","header":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","header_static":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","followers_count":17,"following_count":21,"statuses_count":729,"last_status_at":"2022-02-07","emojis":[],"fields":[{"name":"GitHub","value":"<a href=\"https://github.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">github.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"GitLab","value":"<a href=\"https://gitlab.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">gitlab.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"Blog","value":"<a href=\"https://rubicon.lightstands.xyz\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">rubicon.lightstands.xyz</span><span class=\"invisible\"></span></a>","verified_at":"2020-12-27T15:23:23.054+00:00"},{"name":"Donate (liberapay)","value":"<a href=\"https://liberapay.com/thisLight/donate\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">liberapay.com/thisLight/donate</span><span class=\"invisible\"></span></a>","verified_at":"2021-03-11T00:51:51.566+00:00"}]},"media_attachments":[{"id":"107751441304672354","type":"image","url":"https://files.mastodon.social/media_attachments/files/107/751/441/304/672/354/original/94096d3d3db6de24.png","preview_url":"https://files.mastodon.social/media_attachments/files/107/751/441/304/672/354/small/94096d3d3db6de24.png","remote_url":null,"preview_remote_url":null,"text_url":null,"meta":{"original":{"width":822,"height":164,"size":"822x164","aspect":5.012195121951219},"small":{"width":822,"height":164,"size":"822x164","aspect":5.012195121951219}},"description":null,"blurhash":"U57w]HxvkoxF$,%MoxRi00i{sRS#I;s:r=b^"}],"mentions":[],"tags":[],"emojis":[],"card":null,"poll":null},{"id":"107722294184788555","created_at":"2022-02-01T10:36:04.314Z","in_reply_to_id":null,"in_reply_to_account_id":null,"sensitive":false,"spoiler_text":"","visibility":"public","language":"zh-CN","uri":"https://mastodon.social/users/thislight/statuses/107722294184788555","url":"https://mastodon.social/@thislight/107722294184788555","replies_count":0,"reblogs_count":0,"favourites_count":0,"edited_at":null,"favourited":false,"reblogged":false,"muted":false,"bookmarked":false,"pinned":false,"content":"<p>Crytek宣布了Crysis 4</p><p><a href=\"https://youtu.be/PQ_dmFUR2N8\" rel=\"nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">youtu.be/PQ_dmFUR2N8</span><span class=\"invisible\"></span></a></p>","reblog":null,"application":{"name":"Mastodon for iOS","website":"https://app.joinmastodon.org/ios"},"account":{"id":"150831","username":"thislight","acct":"thislight","display_name":"thislight","locked":false,"bot":false,"discoverable":true,"group":false,"created_at":"2017-05-29T00:00:00.000Z","note":"<p>Developer, Designer.</p>","url":"https://mastodon.social/@thislight","avatar":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","avatar_static":"https://files.mastodon.social/accounts/avatars/000/150/831/original/06a7ee5e88a1e756.jpg","header":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","header_static":"https://files.mastodon.social/accounts/headers/000/150/831/original/31c361d53506a969.png","followers_count":17,"following_count":21,"statuses_count":729,"last_status_at":"2022-02-07","emojis":[],"fields":[{"name":"GitHub","value":"<a href=\"https://github.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">github.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"GitLab","value":"<a href=\"https://gitlab.com/thislight\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">gitlab.com/thislight</span><span class=\"invisible\"></span></a>","verified_at":null},{"name":"Blog","value":"<a href=\"https://rubicon.lightstands.xyz\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">rubicon.lightstands.xyz</span><span class=\"invisible\"></span></a>","verified_at":"2020-12-27T15:23:23.054+00:00"},{"name":"Donate (liberapay)","value":"<a href=\"https://liberapay.com/thisLight/donate\" rel=\"me nofollow noopener noreferrer\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">liberapay.com/thisLight/donate</span><span class=\"invisible\"></span></a>","verified_at":"2021-03-11T00:51:51.566+00:00"}]},"media_attachments":[],"mentions":[],"tags":[],"emojis":[],"card":{"url":"https://www.youtube.com/watch?v=PQ_dmFUR2N8&feature=youtu.be","title":"Crysis 4 (Working Title) Announcement","description":"","type":"video","author_name":"Crysis","author_url":"https://www.youtube.com/user/Crysis","provider_name":"YouTube","provider_url":"https://www.youtube.com/","html":"<iframe width=\"200\" height=\"113\" src=\"https://www.youtube.com/embed/PQ_dmFUR2N8?feature=oembed\" frameborder=\"0\" allowfullscreen=\"\"></iframe>","width":200,"height":113,"image":"https://files.mastodon.social/cache/preview_cards/images/039/018/404/original/3d2f6f20cb265b8a.jpg","embed_url":"","blurhash":"UA7BAmfR9FofxuWBRjof00j[-;ay9Ft7xuWB"},"poll":null}]"""
)


class MastodonUser(object):
    def __init__(
        self,
        mastodon_base_uri: str,
        mastodon_id: str,
        remote_measurement_records_n: int,
        mock_toots: bool,
    ) -> None:
        self.mastodon_id = mastodon_id
        self.api_http_client = AsyncClient(
            base_url="{}/api/".format(mastodon_base_uri), timeout=10
        )
        self.remote_measurement = remote_measurement.RemoteMeasurement(
            remote_measurement_records_n
        )
        self.mock_toots = mock_toots
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
    user: MastodonUser,
    requesting_time: arrow.Arrow,
    t1: float,
    error_type: str,
):
    remote_measurement.push_data(
        user.remote_measurement,
        remote_measurement.MeasurementData(
            time=requesting_time,
            responded=False,
            success=False,
            time_cost=time.perf_counter() - t1,
            error_type=error_type,
        ),
    )


def _get_latest_toots_fake(user: MastodonUser) -> List[Toot]:
    def update_created_at(toot: Toot):
        toot.created_at = arrow.now()
        return toot

    return list(map(update_created_at, map(parse_toot, FAKE_TOOTS_DATA)))


async def _get_latest_toots(user: MastodonUser) -> List[Toot]:
    requesting_time = arrow.get()
    if not user.mock_toots:
        try:
            t1 = time.perf_counter()
            statuses_http_response = await user.api_http_client.get(
                "v1/accounts/{}/statuses".format(user.mastodon_id)
            )
            statuses_http_response.raise_for_status()
        except httpx.TimeoutException as e:
            _push_failing_measurement_data(user, requesting_time, t1, "timeout")
            raise MastodonRemoteUnavailable(
                str(user.api_http_client.base_url), "timeout"
            ) from e
        except httpx.NetworkError as e:
            _push_failing_measurement_data(user, requesting_time, t1, "network")
            raise MastodonRemoteUnavailable(
                str(user.api_http_client.base_url), "network"
            ) from e
        except httpx.HTTPStatusError as e:
            _push_failing_measurement_data(user, requesting_time, t1, "http_status")
            raise MastodonRemoteUnavailable(
                str(user.api_http_client.base_url), "http_status"
            ) from e
        statuses_response: List[Dict[str, Any]] = statuses_http_response.json()
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
                    error_type="response_format_wrong",
                ),
            )
            raise e
        result = list(map(parse_toot, statuses_response))
    else:
        t1 = time.perf_counter()
        result = _get_latest_toots_fake(user)
    remote_measurement.push_data(
        user.remote_measurement,
        remote_measurement.MeasurementData(
            time=requesting_time,
            responded=True,
            success=True,
            time_cost=time.perf_counter() - t1,
        ),
    )
    return result


async def get_latest_toots(user: MastodonUser, *, retries: int = 3) -> List[Toot]:
    tries = retries + 1
    for current_try in range(tries):
        try:
            return await _get_latest_toots(user)
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
        min_success_rate: float = 0.5,
        dryrun: bool = False,
    ) -> None:
        self.tg_bot_token = tg_bot_token
        self.target_chat_identifier = target_chat_identifier
        self.mastodon_user = mastodon_user
        self.last_checked_time = arrow.utcnow()
        self.mastodon_remote_available = False
        self.disable_notification = disable_notification
        self.toots_polling_interval = toots_polling_interval
        self.min_success_rate = min_success_rate
        self.dryrun = dryrun
        super().__init__()


def exact_all_text_from_html(s: str):
    soup = BeautifulSoup(s, "html.parser")
    return soup.get_text(separator="\n")


async def _send_mastodon_remote_error_notification(
    tgbot: aiogram.Bot,
    target_chat: aiogram.types.Chat,
    e: MastodonRemoteUnavailable,
    disable_notification: bool,
    dryrun: bool,
):
    # TODO: send once per hour
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
    if not dryrun:
        await tgbot.send_message(
            target_chat.id, message, disable_notification=disable_notification
        )
    else:
        _logger.info('send message to %s: "%s"', target_chat.id, message)


async def forward_toot(
    tgbot: aiogram.Bot,
    target_chat: aiogram.types.Chat,
    toot: Toot,
    *,
    disable_notification: bool = False,
    dryrun: bool = False,
):
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
    if not dryrun:
        await tgbot.send_message(
            target_chat.id, text_message, disable_notification=disable_notification
        )
    else:
        _logger.info('send message to %s: "%s"', target_chat.id, text_message)


async def _checking_and_forwarding_job(
    bot: TootForwarderBot, tgbot: aiogram.Bot, target_chat: aiogram.types.Chat
):
    _logger.info(
        "Checking new toots. Last checked time: {}.".format(repr(bot.last_checked_time))
    )
    total, forwarded, skipped = 0, 0, 0
    try:
        toots_iter = await get_latest_toots(bot.mastodon_user)
        for toot in toots_iter:
            total += 1
            logging.debug("Processing toot: %s", toot)
            if toot.created_at > bot.last_checked_time:
                _logger.info("Forwarding %s.", toot)
                forwarded += 1
                await forward_toot(
                    tgbot,
                    target_chat,
                    toot,
                    disable_notification=bot.disable_notification,
                    dryrun=bot.dryrun,
                )
                bot.last_checked_time = toot.created_at
            else:
                skipped += 1
        bot.mastodon_remote_available = True
    except MastodonRemoteUnavailable as e:
        snapshot = remote_measurement.capture_measurement(
            bot.mastodon_user.remote_measurement
        )
        if (snapshot.success_rate < bot.min_success_rate) and (
            not bot.mastodon_remote_available
        ):
            await _send_mastodon_remote_error_notification(
                tgbot,
                target_chat,
                e,
                disable_notification=bot.disable_notification,
                dryrun=bot.dryrun,
            )
        if e.error_type != "timeout" or (
            snapshot.the_most_happened_error_type == "timeout"
            and snapshot.the_most_happened_error_rate
            and snapshot.the_most_happened_error_rate >= 0.8
        ):
            bot.mastodon_remote_available = False
        _logger.error(
            "Mastodon remote %s is unavailable? Responded %s%% (success %s%%) in %s to %s (as %s)",
            e.remote,
            snapshot.responded_rate,
            snapshot.success_rate,
            snapshot.time_start,
            snapshot.time_end,
            snapshot.time_delta,
            exc_info=e,
        )
    _logger.info(
        "Done! Total/Forwarded/Skipped: {}/{}/{}. {}".format(
            total,
            forwarded,
            skipped,
            remote_measurement.capture_measurement(
                bot.mastodon_user.remote_measurement
            ),
        )
    )


def _schedule_toot4warder_cothread(
    bot: TootForwarderBot, tgbot: aiogram.Bot
) -> asyncio.Task:
    async def toot4warder_cothread():
        _logger.info("Getting chat of '{}'.".format(bot.target_chat_identifier))
        target_chat = await tgbot.get_chat(bot.target_chat_identifier)
        while True:
            await asyncio.sleep(bot.toots_polling_interval, None)
            await _checking_and_forwarding_job(bot, tgbot, target_chat)

    return asyncio.create_task(toot4warder_cothread())


async def create_updater(bot: TootForwarderBot) -> aiogram.Dispatcher:
    tgbot = aiogram.Bot(bot.tg_bot_token)
    _schedule_toot4warder_cothread(bot, tgbot)
    dispatcher = aiogram.Dispatcher(tgbot)
    return dispatcher
