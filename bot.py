import asyncio

import disnake
from disnake import LoginFailure
from disnake.ext import commands

from config import get_setting, set_setting
from console_colors import YELLOW, RESET, RED
from db import create_tables

def create_bot():
    intents = disnake.Intents.default()
    intents.message_content = True
    intents.reactions = True
    intents.members = True
    return commands.InteractionBot(intents=intents)


EXTENSIONS = (
    "cogs.lifecycle",
    "cogs.reminder",
    "cogs.send_reminders",
)


def load_extensions(bot) -> None:
    for ext in EXTENSIONS:
        print(f"[INFO]{YELLOW} Loading {ext.replace('cogs.', '')}{RESET}")
        try:
            bot.load_extension(ext)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to load extension {ext}: {e}")
            raise


def main():
    create_tables()

    while True:
        token = get_token()
        bot = create_bot()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            load_extensions(bot)
            bot.run(token)
            break
        except LoginFailure:
            print(f"{RED}[ERROR] Invalid token.{RESET}")
            set_setting("token", None)


def get_token():
    token = get_setting("token")
    # If not user token, take user input from console
    while not token:
        print(f"{RED}[ERROR] Valid Discord token not set!{RESET}")
        print(f"{YELLOW}To get a token, visit https://discord.com/developers/applications{RESET}")
        print(f"{YELLOW}Please enter your token...{RESET}")
        token = input().strip()
        set_setting("token", token)
    return token

if __name__ == "__main__":
    main()