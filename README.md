# tg_toot4warder
A toot forwarder for telegram channel.

## How to use

0. Install poetry
1. `poetry install`
2. Set environment variables:
    - `MASTODON_INSTANCE` for instance address. For example `https://mastodon.social`.
    - `MASTODON_ID`: your unique id in the instance. It's a integer, you may find it on your profile page's uri.
    - `BOT_TOKEN`: telegram bot access token.
    - `TARGET_CHAT_ID`: the channel's identitifer, currently only username (include the prefixed `@`).
3. Run the bot: `poetry run python -m tg_toot4warder`.

## License
AGPL-3.0-or-later
