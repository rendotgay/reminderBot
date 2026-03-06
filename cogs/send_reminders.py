from datetime import datetime, timezone, timedelta

from disnake import Embed
from disnake.ext import commands
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from colors import get_color_from_priority
from console_colors import RED, YELLOW, RESET, GREEN
from db import get_user, get_reminders, delete_reminder, update_reminder_time
from util import _as_aware_utc, compute_next_due, update_users
from views import ReminderView


class SendReminderCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})


    @staticmethod
    def _job_id(creator:int, remindee:int, title:str) -> str:
        return f"reminder:{creator}:{remindee}:{title.lower()}"


    async def send_reminder(
            self,
            creator,
            remindee,
            time,
            frequency,
            title,
            message,
            priority,
            destination
    ):
        update_users(self.bot, target=creator)
        color = get_color_from_priority(priority)
        creator = get_user(creator)
        embed = Embed(
            title=title,
            description=message,
            color=color,
            timestamp=time,
        )
        embed.set_author(name=creator['display_name'], icon_url=creator['avatar_url'])
        view = ReminderView(creator['id'], remindee, title, embed, frequency)
        try:
            remindee = await self.bot.fetch_user(remindee)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to fetch user {YELLOW}{remindee}{RED}: {e}{RESET}")
            return
        if destination and destination != "Direct Message":
            try:
                channel = await self.bot.fetch_channel(destination)
                await channel.send(content=remindee.mention, embed=embed, view=view)
                if frequency.lower() != "once":
                    await self.reschedule(creator['id'], remindee.id, time, frequency, title, message, priority, destination)
                return
            except Exception as e:
                print(f"{RED}[ERROR] Failed to send reminder to {YELLOW}{remindee.display_name}{RED} in {YELLOW}{destination}{RED}: {e}{RESET}")
        try:
            await remindee.send(embed=embed, view=view)
            if frequency.lower() != "once":
                await self.reschedule(creator['id'], remindee.id, time, frequency, title, message, priority, destination)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to send reminder to {YELLOW}{remindee.display_name}{RED}: {e}{RESET}")
            return


    def _schedule_one(
            self,
            creator,
            remindee,
            time,
            frequency,
            title,
            message,
            priority,
            destination
    ):
        run_at = _as_aware_utc(time)
        jid = self._job_id(creator, remindee, title)

        print(f"{GREEN}scheduled {YELLOW}{jid}{GREEN} at {YELLOW}{run_at.isoformat()}{RESET}")

        self.scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=run_at,
            args=[creator, remindee, time, frequency, title, message, priority, destination],
            id=jid,
            replace_existing=True,
            misfire_grace_time=60 * 10,
        )


    async def load_persistent_reminders(self):
        reminders = get_reminders()
        now = datetime.now(timezone.utc)

        for row in reminders:
            creator, remindee, time, frequency, title, message, priority, destination, completed = row
            due = _as_aware_utc(datetime.fromisoformat(time))
            if due <= now:
                due = now + timedelta(seconds=5)
            self._schedule_one(creator, remindee, due, frequency, title, message, priority, destination)


    async def reschedule(self, creator, remindee, time, frequency, title, message, priority, destination):
        if frequency.lower() == "once":
            return
        now = datetime.now(timezone.utc)
        next_due = compute_next_due(now, time, frequency)
        update_reminder_time(creator, remindee, next_due)
        self._schedule_one(creator, remindee, next_due, frequency, title, message, priority, destination)


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{GREEN}Reminders loaded!{RESET}")
        if not self.scheduler.running:
            self.scheduler.start()
        await self.load_persistent_reminders()


def setup(bot: commands.InteractionBot):
    bot.add_cog(SendReminderCog(bot))

