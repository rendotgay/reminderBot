import disnake
from disnake.ext import commands

from console_colors import GREEN, YELLOW, RESET, CYAN
from db import set_user_locale, get_incomplete_reminders
from util import update_users


class LifecycleCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_presence()
        print(f"[INFO] {CYAN}Logged in as {GREEN}{self.bot.user}{CYAN}!{RESET}")
        update_users(self.bot)


    async def update_presence(self):
        reminder_count = get_incomplete_reminders()
        await self.bot.change_presence(
            activity=disnake.CustomActivity(name=f"{reminder_count} incomplete reminder{'s' if int(reminder_count) != 1 else ''}!")
        )


    # Store user data for future use
    @commands.Cog.listener()
    async def on_interaction(self, inter: disnake.Interaction):
        u = getattr(inter, "user", None)
        if u:
            locale = str(getattr(inter, "locale", None)) if getattr(inter, "locale", None) else None
            if locale:
                set_user_locale(u.id, locale)
        update_users(self.bot, target=u)


    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        print(f"[INFO] {GREEN}Bot joined new server: {YELLOW}{guild.name}{RESET}")
        update_users(self.bot, target=guild)


    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        print(f"[INFO] {GREEN}New member {YELLOW}{member.name}{GREEN} joined {YELLOW}{member.guild.name}{RESET}")
        update_users(self.bot, target=member)


def setup(bot: commands.InteractionBot):
    bot.add_cog(LifecycleCog(bot))
