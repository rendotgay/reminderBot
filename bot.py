import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

from config import get_setting
from db import create_tables

intents = disnake.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.InteractionBot(intents=intents)
# bot.i18n.load("locale/")

EXTENSIONS = (
    "cogs.lifecycle",
    "cogs.reminder",
    "cogs.send_reminders",
)

def load_extensions() -> None:
    for ext in EXTENSIONS:
        try:
            bot.load_extension(ext)
        except Exception as e:
            print(f"[ERROR] Failed to load extension {ext}: {e}")
            raise

def main() -> None:
    token = get_setting("token")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set")

    create_tables()
    load_extensions()
    bot.run(token)

# async def start(token):
#     print("Starting bot...")
#     create_tables()
#     load_extensions()
#     await bot.start(token)

if __name__ == "__main__":
    main()
