from datetime import datetime, timezone, timedelta

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from disnake import Embed
from disnake.ext import commands

from console_colors import RED, YELLOW, RESET, GREEN, CYAN
from db import get_user, get_reminders, update_reminder_time, update_reminder_limit, is_reminder_completed
from util import _as_aware_utc, compute_next_due, update_users, get_color_from_priority
from views import ReminderView


class SendReminderCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})


    # Scheduler job ID's
    @staticmethod
    def _job_id(creator:int, remindee:int, title:str) -> str:
        return f"reminder:{creator}:{remindee}:{title.lower()}"

    @staticmethod
    def _pester_job_id(creator: int, remindee: int, title: str) -> str:
        return f"pester:{creator}:{remindee}:{title.lower()}"


    # Send reminders
    async def send_reminder(
            self,
            creator,
            remindee,
            time,
            frequency,
            title,
            message,
            priority,
            destination,
            limit,
            pester
    ):
        # Get up to date user data
        update_users(self.bot, target=creator)
        # Build response
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
        # Attempt to send server reminders
        if destination and destination != "Direct Message":
            try:
                channel = await self.bot.fetch_channel(destination)
                await channel.send(content=remindee.mention, embed=embed, view=view)
                if frequency.lower() != "once":
                    await self.reschedule(creator['id'], remindee.id, time, frequency, title, message, priority, destination, limit, pester)
                if pester:
                    self._schedule_pester(creator['id'], remindee.id, time, frequency, title, message, priority, destination, limit, pester)
                return
            except Exception as e:
                print(f"{RED}[ERROR] Failed to send reminder to {YELLOW}{remindee.display_name}{RED} in {YELLOW}{destination}{RED}: {e}{RESET}")
        # Fallback to DM if no channel found or DM is specified
        try:
            await remindee.send(embed=embed, view=view)
            if frequency.lower() != "once":
                await self.reschedule(creator['id'], remindee.id, time, frequency, title, message, priority, destination, limit, pester)
            if pester:
                self._schedule_pester(creator['id'], remindee.id, time, frequency, title, message, priority, destination, limit, pester)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to send reminder to {YELLOW}{remindee.display_name}{RED}: {e}{RESET}")
            return


    # Schedule reminders and pesters
    def _schedule_pester(self, creator_id: int, remindee_id: int, time, frequency, title, message, priority, destination, limit, pester):
        now = datetime.now(timezone.utc)
        next_pester = compute_next_due(now, now, pester)
        job_id = self._pester_job_id(creator_id, remindee_id, title)
        print(f"[SCHEDULER] {GREEN}pester scheduled {YELLOW}{title}{GREEN} at {YELLOW}{next_pester.strftime('%A, %B %d %Y %I:%M %p')} UTC{RESET}")
        self.scheduler.add_job(
            self.send_pester,
            "date",
            run_date=next_pester,
            args=[creator_id, remindee_id, time, frequency, title, message, priority, destination, limit, pester],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=60 * 10,
        )

    async def send_pester(self, creator_id, remindee_id, time, frequency, title, message, priority, destination, limit, pester):
        if is_reminder_completed(creator_id, remindee_id, title):
            print(f"[INFO] {GREEN}pester stopped for {YELLOW}{title}{GREEN} — marked complete{RESET}")
            return
        await self.send_reminder(creator_id, remindee_id, time, frequency, title, message, priority, destination, limit, pester)

    def _schedule_one(
            self,
            creator,
            remindee,
            time,
            frequency,
            title,
            message,
            priority,
            destination,
            limit,
            pester
    ):
        run_at = _as_aware_utc(time)
        job_id = self._job_id(creator, remindee, title)

        print(f"[SCHEDULER] {GREEN}scheduled {YELLOW}{title}{GREEN} at {YELLOW}{run_at.strftime("%A, %B %d %Y %I:%M %p")} UTC{RESET}")

        self.scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=run_at,
            args=[creator, remindee, time, frequency, title, message, priority, destination, limit, pester],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=60 * 10,
        )


    async def load_persistent_reminders(self):
        reminders = get_reminders()
        now = datetime.now(timezone.utc)

        for row in reminders:
            creator, remindee, time, frequency, pester, limit, title, message, priority, destination, completed = row
            try:
                due = _as_aware_utc(datetime.fromisoformat(time))
            except TypeError:
                due = datetime.now(timezone.utc)
            if completed and frequency.lower() == "once":
                continue
            if limit and limit <= 0:
                continue
            if due <= now:
                due = now + timedelta(seconds=5)
            self._schedule_one(creator, remindee, due, frequency, title, message, priority, destination, limit, pester)
            if pester and not completed:
                self._schedule_pester(creator, remindee, due, frequency, title, message, priority, destination, limit, pester)
        print(f"[DB] {CYAN}Loaded {GREEN}{len(reminders)}{CYAN} persistent reminder{'s' if len(reminders) != 1 else ''}{RESET}")


    async def reschedule(self, creator, remindee, time, frequency, title, message, priority, destination, limit, pester):
        if frequency.lower() == "once":
            return
        now = datetime.now(timezone.utc)
        next_due = compute_next_due(now, time, frequency)
        update_reminder_time(creator, remindee, next_due)
        update_reminder_limit(creator, remindee, limit - 1)
        self._schedule_one(creator, remindee, next_due, frequency, title, message, priority, destination, limit, pester)


    @commands.Cog.listener()
    async def on_ready(self):
        if not self.scheduler.running:
            self.scheduler.start()
        await self.load_persistent_reminders()


def setup(bot: commands.InteractionBot):
    bot.add_cog(SendReminderCog(bot))