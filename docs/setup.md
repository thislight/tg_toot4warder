# How to setup tg_toot4warder

In this tutorial, I assume your machine for hosting tg_toot4warder is:

- "Ubuntu 20.04" 
- All packages are latest

And we will use systemd to managing tasks, to ensure if your system having systemd, run `systemd --version`. If the command works without any message like "command not found", your system have systemd -- but all Ubuntu 20.04 **have** systemd (so you, if using Ubuntu 20.04, don't need to check if you have systemd).

## Step 0: Prepare environment

Update local package index for apt:

````shell
sudo apt update
````

You will need [Git](https://git-scm.org) to clone this project, [Python](https://python.org) 3.7+ to run the program, [Poetry](https://python-poetry.org) to make bundle can be installed:

````shell
sudo apt install git python3 python3-pip
````

And follow [documentation on poetry website](https://python-poetry.org/docs/) to install poetry, just one line command in short:

````shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
````

Follow the notes on the screen.

Then, let's have a look on versions:

````shell
git --version
# -> git version 2.25.1
python3 -V
# -> Python 3.8.10
poetry --version
# -> Poetry version 1.1.6
````

## Step 1: Clone project

It's simple. Clone the project by git:

````shell
git clone https://github.com/thislight/tg_toot4warder.git
````

Then we enter the directory:

````shell
cd tg_toot4warder
````

## Step 2: Filling infomation

There are two files in "systemd-unit":

````
systemd-unit/
├── tg_toot4warder.env
└── tg_toot4warder.service
````

Later we will copy them to different places. Let's begin with `tg_toot4warder.env`. In first step, we will copy the file to another place. I will copy to home directory:

````shell
cp systemd-unit/tg_toot4warder.env ~
````

Let's have look to the copied "tg_toot4warder.env". We have four fields to fill there:

````shell
MASTODON_INSTANCE="https://mastodon.example"
MASTODON_ID="<your unique integer id on the instance>"
BOT_TOKEN="<telegram bot token>"
TARGET_CHAT="<channel username>"
````

Fill your mastodon instance in `MASTODON_INSTANCE`. I use https://mastodon.social in this case.

````shell
MASTODON_INSTANCE="https://mastodon.social"
````

Then, we need to fill account unique integer id on the instance. There is a way: open your profile page in browser, and you will got a address like "https://mastodon.social/web/accounts/150831", the number in the end is your id.

````shell
MASTODON_ID="150831"
````

Fill your telegram bot token in `BOT_TOKEN`. You can get one on [BotFather](https://t.me/BotFather).

````shell
BOT_TOKEN="xxxx:xxx"
````

...And finally the channel username you want to forwarded to.

````shell
TARGET_CHAT="@thislight"
````

That's our "tg_toot4warder.env" (and we don't need to original one then):

````shell
MASTODON_INSTANCE="https://mastodon.social"
MASTODON_ID="150831"
BOT_TOKEN="<telegram bot token>"
TARGET_CHAT="@thislight"
````

To protect the file being accessed from other users, I change it's permission to `600`:

````shell
chmod 0600 tg_toot4warder.env
````

## Step 3: Install tg_toot4warder

Use `poetry build` to make bundle, then you can find some files in "dist":

````
dist
├── tg_toot4warder-0.1.0a2-py3-none-any.whl
└── tg_toot4warder-0.1.0a2.tar.gz
````

We will install tg_toot4warder thought the file which the name is ended with ".whl".

Use pip:

````shell
sudo pip3 install dist/tg_toot4warder-0.1.0a2-py3-none-any.whl
````

We could run `tg_toot4warder --help` to ensure it have installed.

````shell
tg_toot4warder --help
````

The output looks like:

````
Usage: tg_toot4warder [OPTIONS]

Options:
  --instance TEXT                 Mastodon instance address. (accept
                                  environment variable MASTODON_INSTANCE)
                                  [required]
  --id INTEGER                    Your unique integer on the instance. (accept
                                  environment variable MASTODON_ID)
                                  [required]
  --bot-token TEXT                Access token for telegram bot. (accept
                                  environment variable BOT_TOKEN)  [required]
  --target-chat TEXT              Identifier for the chat, may be the username
                                  (with prefix "@") or integer. (accept
                                  environment variable TARGET_CHAT_ID)
                                  [required]
  --verbose / --no-verbose        Print out more verbose debugging message.
  --disable-notification / --enable-notification
                                  Should the telegram message have
                                  notification. (accept environment variable
                                  DISABLE_NOTIFICATION)
  --toots-polling-interval INTEGER
                                  The polling interval in seconds for toots,
                                  the default is 60. (accept environment
                                  variable TOOTS_POLLING_INTERVAL)
  --help                          Show this message and exit.
````


## Step 4: Set up service

Copy "tg_toot4warder.service" in systemd-unit to `/etc/systemd/system`:

````shell
cp systemd-unit/tg_toot4warder.service /etc/systemd/system
````

But it could not be used now, we need make a small change to link it to the infomation we just filled: open the copied "tg_toot4warder.service", find this line:

````
EnvironmentFile=/path/to/tg_toot4warder.env
````

Change the "/path/to/tg_toot4warder.env" to the path to our "tg_toot4warder.env". In my case it's "~/tg_toot4warder.env", but we need absolute path here, the path would be "/home/ubuntu/tg_toot4warder.env".

````
EnvironmentFile=/home/ubuntu/tg_toot4warder.env
````

But now the service could not access the file we specified, we need this service being run in our user. Add these lines under `[Service]`:

````
User=<your username>
Group=<your user group>
````

But how can we figure out the username and the user group? Use command `id`, the output looks like:

````shell
id
# -> uid=1001(ubuntu) gid=1001(ubuntu) groups=1001(ubuntu),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),117(netdev),118(lxd)
````

Look at `uid=` and `gid=`, the contents in brackets is your username and user group filled here. In this case they are `ubuntu`.

````
User=ubuntu
Group=ubuntu
````

Ok, here we are! Now enable the service in systemd:

````shell
sudo systemctl enable tg_toot4warder
````

Start the service:

````shell
sudo systemctl start tg_toot4warder
````

Now you can look at the log though `systemctl` or `journalctl`.

````shell
sudo systemctl status tg_toot4warder
````

Or:

````shell
sudo journalctl -u tg_toot4warder
````
