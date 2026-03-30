import re
from datetime import datetime, timedelta, timezone
from typing import List

import dateparser
import disnake
import pytz
from disnake import Embed, OptionChoice
from disnake.ext import commands

from config import get_setting
from console_colors import RED, RESET
from db import add_reminder, get_user_tz, get_last_location, get_previous_locations, get_users_reminders
from util import update_users, compute_next_due, normalize_frequency, get_color_from_priority


class ReminderCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    # Parse user input for frequencies
    @staticmethod
    async def auto_frequency(
            inter: disnake.ApplicationCommandInteraction,
            current: str,
    ) -> List[str]:
        string = current.lower().strip()
        options = ["once"]

        intervals = [
            "hourly",
            "daily",
            "weekly",
            "every other week",
            "monthly",
            "every other month"
        ]

        units = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
            "nineteen": 19
        }

        tens = {
            "twenty": 20, "thirty": 30, "forty": 40,
            "fifty": 50, "sixty": 60, "seventy": 70,
            "eighty": 80, "ninety": 90
        }

        num_pattern = r"\b\d+\.\d+\b|\b\d+"
        all_nums = re.findall(num_pattern, string)

        tokens = re.findall(r"\b[a-z]+\b", string)

        i = 0
        while i < len(tokens):
            word = tokens[i]

            if word in tens:
                value = tens[word]
                if i + 1 < len(tokens) and tokens[i + 1] in units:
                    value += units[tokens[i + 1]]
                    i += 1
                all_nums.append(str(value))

            elif word in units:
                all_nums.append(str(units[word]))

            i += 1

        if all_nums:
            for num in all_nums:
                options.append(f"{num} times per hour")
                options.append(f"every {num} hours")
                options.append(f"{num} times per day")
                options.append(f"every {num} days")
                options.append(f"{num} times per week")
                options.append(f"every {num} weeks")

        for i in intervals:
            if string in i:
                options.append(i)

        return options[:25]


    # Provide locations to send reminders
    async def auto_destination(
            self,
            inter: disnake.ApplicationCommandInteraction,
            current: str,
    ) -> List[str]:
        c = current.lower().strip()
        seen = set()
        d = []
        if c in "here":
            d.append(OptionChoice(name="Here", value=str(inter.channel.id)))
        last_location = get_last_location(inter.user.id)
        if c in "last" and last_location:
            d.append(OptionChoice(name="Last", value=str(last_location[0])))
        if c in "dm" or c in "direct message":
            d.append(OptionChoice(name="Direct Message", value="Direct Message"))
        previous_locations = get_previous_locations(inter.user.id)
        for location in previous_locations:
            location = location[0]
            if location != "Direct Message":
                channel = await self.bot.fetch_channel(int(location))
                if channel and c in channel.name.lower():
                    seen.add(channel.id)
                    d.append(OptionChoice(name=f"#{channel.name}", value=str(channel.id)))
        if type(inter.channel) != disnake.DMChannel:
            guild = inter.guild
            for channel in guild.text_channels:
                if channel.id not in seen and c in channel.name.lower():
                    d.append(OptionChoice(name=f"#{channel.name}", value=str(channel.id)))
        if current:
            d = sorted(d, key=lambda choice: (choice.name.lower().find(c), choice.name.lower()))
        return d[:25]


    # TODO: Replace with custom date parser, but this works fine for it's use case
    # Get date and time from user input
    @staticmethod
    async def auto_time(
            inter: disnake.ApplicationCommandInteraction,
            current: str,
    ):
        tz = get_user_tz(inter.user.id)
        if not tz:
            tz = get_setting("default_timezone")
        if current == "" or current == "now":
            now = datetime.now(pytz.timezone(tz))
            return [OptionChoice(name="Now", value=str(now))]
        else:
            settings = {'TIMEZONE': tz, 'RETURN_AS_TIMEZONE_AWARE': True}
            parsed_time = dateparser.parse(current, settings=settings)
            if parsed_time is None:
                now = datetime.now(pytz.timezone(tz))
                return [OptionChoice(name="Now", value=str(now))]
            else:
                return [OptionChoice(name=parsed_time.strftime("%A, %B %d %Y %I:%M %p"), value=str(parsed_time))]


    # Sub command for reminders, allows commands to start with "/reminder "
    @commands.slash_command(
        name="reminder",
        description="Manage reminders"
    )
    @commands.install_types(guild=True, user=True)
    @commands.contexts(guild=True, bot_dm=True, private_channel=True)
    async def reminder(self, inter):
        pass


    # Create new reminders
    @reminder.sub_command(
        name="create",
        description="Create a new reminder"
    )
    async def reminder_create(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User | disnake.Member,
            frequency: str = commands.Param(
                description="How often should this reminder occur?",
                autocomplete=auto_frequency
            ),
            pester: str = commands.Param(
                description="[WIP] How often to send follow up reminders if not completed?",
                autocomplete=auto_frequency,
                default=None
            ),
            limit: int = commands.Param(
                description="How many times should this reminder occur?",
                default=None
            ),
            time: str = commands.Param(
                description="When should this reminder occur?",
                autocomplete=auto_time,
                default=None,
            ),
            title: str = commands.Param(
                description="Name to give the reminder?",
            ),
            message: str = commands.Param(
                description="Extra details about the reminder?",
                default=""
            ),
            priority: str = commands.Param(
                description="How important is this reminder?",
                choices=["low", "medium", "high"],
                default="low"
            ),
            destination: str = commands.Param(
                description="Where should this reminder be sent?",
                autocomplete=auto_destination,
                default=get_setting("default_reminder_option"),
            ),
            hide_message: bool = commands.Param(
                description="Hide the confirmation message of this command?",
                default=get_setting("hide_confirmation_message").lower() == "true",
            ),
    ):
        # Get up to date user data
        update_users(self.bot, target=user)

        # Parse destination
        if destination == "Here":
            destination = inter.channel.id

        if destination == "Default":
            destination = get_setting("default_reminder_channel")
            # Fallback to "Here" if no default reminder channel is set
            if not destination:
                print(f"{RED}[ERROR] No default reminder channel set")
                destination = inter.channel.id
        if destination == "Last":
            destination = get_last_location(inter.user.id)
            # Fallback to "Default" if no last location
            if not destination:
                destination = get_setting("default_reminder_channel")
                # Fallback to "Here" if no default reminder channel is set
                if not destination:
                    destination = inter.channel.id

        # Parse datetime
        if time:
            try:
                time = datetime.fromisoformat(time)
            except ValueError:
                try:
                    time = datetime.strptime(time, "%A, %B %d %Y %I:%M %p")
                # If parsing fails, send error message instead of defaulting to now to avoid incorrectly timed reminders
                except Exception as e:
                    print(f"{RED}[ERROR] Failed to parse time: {e}{RESET}")
                    embed = Embed(
                        color=get_color_from_priority("high"),
                        title="Error",
                        description=f"Failed to parse time for reminder: {e}"
                    )
                    await inter.response.send_message(
                        embed=embed,
                        ephemeral=True,
                    )
                    return
        # Default to now if no time is provided
        else:
            time = datetime.now(timezone.utc)
        # Get next due time from frequency and datetime
        now = datetime.now(timezone.utc)
        if now + timedelta(minutes=5) >= time.astimezone(timezone.utc):
            if frequency.lower() != "once":
                frequency = normalize_frequency(frequency)
                time = compute_next_due(now, time, frequency)
            else:
                time = now
        pester = normalize_frequency(pester) if pester else None
        # Insert and schedule reminder
        try:
            add_reminder(
                creator_id=inter.user.id,
                remindee_id=user.id,
                time=time,
                frequency=frequency,
                title=title,
                message=message,
                priority=priority,
                destination=destination,
                limit=limit,
                pester=pester,
            )
            send_cog = self.bot.get_cog("SendReminderCog")
            send_cog._schedule_one(
                creator=inter.user.id,
                remindee=user.id,
                time=time,
                frequency=frequency,
                title=title,
                message=message,
                priority=priority,
                destination=destination,
                limit=limit,
                pester=pester
            )
            if pester:
                send_cog._schedule_pester(
                    creator_id=inter.user.id,
                    remindee_id=user.id,
                    time=time,
                    frequency=frequency,
                    title=title,
                    message=message,
                    priority=priority,
                    destination=destination,
                    limit=limit,
                    pester=pester,
                )
            # Build response
            description = [
                f"Reminder created for {user.mention}."
            ]
            if message:
                description.append(f'*"{message}"*',)
            embed = Embed(
                color=get_color_from_priority("low"),
                title=title,
                description="\n".join(description),
                timestamp=time,
            )
            embed.set_author(name="Reminder created!")
            embed.set_footer(text="Next reminder")
        except Exception as e:
            print(f"{RED}[ERROR] Failed to create reminder: {e}{RESET}")
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"Failed to create reminder: {e}"
            )
            hide_message = True
        await inter.response.send_message(
            embed=embed,
            ephemeral=hide_message,
        )

    # List of users reminders
    @reminder.sub_command(
        name="list",
        description="List reminders"
    )
    async def reminder_list(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User | disnake.Member = commands.Param(
                description="Who's reminders should be listed?",
                default=None,
            ),
            completed: bool = commands.Param(
                description="Show completed reminders?",
                default=False,
            ),
            hide_message: bool = commands.Param(
                description="Hide your reminder list",
                default=get_setting("hide_list_message").lower() == "true",
            )
    ):
        reminders = get_users_reminders(user.id if user else inter.user.id, completed)
        if not reminders:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="No reminders",
                description=f"{user.display_name + " has" if user else 'You have'} no reminders."
            )
            await inter.response.send_message(embed=embed, ephemeral=hide_message)
            return
        # Build response
        creators = {}
        reminder_list = []
        for reminder in reminders:
            if reminder["creator"] not in creators:
                creator = await self.bot.fetch_user(reminder["creator"])
                creators[reminder["creator"]] = creator
            else:
                creator = creators[reminder["creator"]]
            completed_string = "~~" if reminder["completed"] else ""
            reminder_list.append(f"{completed_string}**{creator.display_name}**: {reminder['title']}{completed_string}")

        embed = Embed(
            color=get_color_from_priority("low"),
            title=f"{user.display_name if user else inter.user.display_name}'s reminders",
            description="\n".join(reminder_list)
        )
        await inter.response.send_message(embed=embed, ephemeral=hide_message)


def setup(bot: commands.InteractionBot):
    bot.add_cog(ReminderCog(bot))