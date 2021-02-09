# bot.py
import importlib
import sys
import os
import random
import shlex
import shutil
import subprocess
import traceback
import psutil
from telegram.ext import Updater
from telegram import ChatAction
from telegram import Bot
from telegram.parsemode import ParseMode

# import sugaroid_commands as scom
from datetime import datetime
from nltk import word_tokenize
import sugaroid as sug
from sugaroid import sugaroid
from sugaroid import version
from dotenv import load_dotenv
import time
from datetime import timedelta

# get CPU data
process = psutil.Process()
init_cpu_time = process.cpu_percent()

# get the environment variables
load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")

# initialize sugaroid and use discord like spec
sg = sugaroid.Sugaroid()
sg.toggle_discord()

# telegram specific stuff
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

# get the start time
interrupt_local = False
start_time = datetime.now()

message_length_limit = 4000


def split_into_packets(response: str) -> list:
    messages = []
    for i in range(0, len(response), message_length_limit):
        messages.append(response[i : i + message_length_limit])

    broken_messages = []
    for message in messages:
        broken_messages.extend(message.split("<br>"))

    return broken_messages


def update_sugaroid(update, context, branch="master"):
    # initiate and announce to the user of the upgrade
    context.bot.send_message(
        update.effective_chat.id, "Updating my brain with new features 😄"
    )

    # execute pip3 install
    pip = shutil.which("pip")
    pip_popen_subprocess = subprocess.Popen(
        shlex.split(
            f"{pip} install --upgrade --force-reinstall --no-deps "
            f"https://github.com/srevinsaju/sugaroid/archive/{branch}.zip"
        ),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # reload modules
    os.chdir("/")
    importlib.reload(sug)
    importlib.reload(sugaroid)
    importlib.reload(version)

    # updating the bot
    os.chdir(os.path.dirname(sug.__file__))
    git = shutil.which("git")
    # reset --hard
    git_reset_popen_subprocess = subprocess.Popen(
        shlex.split(f"{git} reset --hard origin/master"),
        stdout=sys.stdout,
        stderr=sys.stderr,
    ).wait(500)
    # git pull
    git_pull_popen_subprocess = subprocess.Popen(
        shlex.split(f"{git} pull"), stdout=sys.stdout, stderr=sys.stderr
    )

    context.bot.send_message(
        update.effective_chat.id,
        "Update completed. 😄, Restarting myself  💤",
        parse_mode=ParseMode.HTML,
    )
    sys.exit(1)


def on_ready():
    os.chdir(os.path.dirname(sug.__file__))


def on_message(update, context):
    # if message.author == client.user:
    #    print("Ignoring message sent by another Sugaroid Instance")
    #     return
    global interrupt_local

    if update.effective_message.chat_id not in [-1001464483235, -1001281270626]:
        print("Message from invalid chat ID", update.effective_message.chat_id)
        return

    if (
        update.message is not None
        and update.message.text is not None
        and any(
            (
                update.message.text.startswith(f"@{context.bot.getMe().username}"),
                update.message.text.startswith("!S"),
            )
        )
    ):
        # make the user aware that Sugaroid received the message
        # send the typing status
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING
        )

        # clean the message
        msg = (
            update.message.text.replace(f"@{context.bot.getMe().username}", "")
            .replace("!S", "")
            .strip()
        )

        if "update" in msg and len(msg) <= 7:
            if message.from_user.username == "srevinsaju":
                parts = msg.split()[-1]
                if parts.lower() == "update":
                    parts = "master"
                update_sugaroid(message, updater)
            else:
                # no permissions
                context.bot.send_message(
                    update.effective_chat.id,
                    "I am sorry. I would not be able to update myself.\n"
                    "Seems like you do not have sufficient permissions",
                    parse_mode=ParseMode.HTML,
                )
            return
        elif "stop" in update.message.text and "learn" in update.message.text:
            if str(message.from_user.username) == "srevinsaju":
                global interrupt_local
                interrupt_local = False
                context.bot.send_message(
                    update.effective_chat.id,
                    "InterruptAdapter terminated",
                    parse_mode=ParseMode.HTML,
                )
            else:
                context.bot.sed_message(
                    update.effective_chat.id,
                    "I am sorry. I would not be able to update myself.\n"
                    "Seems like you do not have sufficient permissions",
                    parse_mode=ParseMode.HTML,
                )
            return
        lim = 4095
        try:
            response = str(sg.parse(msg))
        except Exception as e:
            # some random error occured. Log it
            error_message = traceback.format_exc(chain=True)
            response = (
                '<pre language="python">'
                "An unhandled exception occurred: " + error_message + "</pre>"
            )
        for packet in split_into_packets(str(response)):
            context.bot.send_message(
                update.effective_chat.id, packet, parse_mode=ParseMode.HTML
            )

    elif interrupt_local:
        token = word_tokenize(update.message.text)
        for i in range(len(token)):
            if str(token[i]).startswith("@"):
                token.pop(i)
        if len(token) <= 5:
            messages = " ".join(token)
            author = message.author.mention
            sg.append_author(author)
            sg.interrupt_ds()
            response = sg.parse(messages)
            print(response, "s" * 5)
            context.bot.send_message(
                update.effective_chat.id, str(response), parse_mode=ParseMode.HTML
            )
        return


from telegram.ext import MessageHandler, Filters

on_message_handler = MessageHandler(Filters.text & (~Filters.command), on_message)
dispatcher.add_handler(on_message_handler)
updater.start_polling()
updater.idle()
