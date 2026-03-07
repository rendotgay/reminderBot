import disnake
from disnake.ext import commands

from config import get_setting
from console_colors import YELLOW, RESET, RED
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
        print(f"{YELLOW}[INFO] Loading {ext.replace('cogs.', '')}{RESET}")
        try:
            bot.load_extension(ext)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to load extension {ext}: {e}")
            raise

def main() -> None:
    token = get_setting("token")
    if not token:
        raise RuntimeError(f"{RED}[ERROR] DISCORD_TOKEN not set{RESET}")

    create_tables()
    load_extensions()
    bot.run(token)

if __name__ == "__main__":
    main()
