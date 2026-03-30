from disnake import ButtonStyle, MessageInteraction, Embed
from disnake.ui import View, button, Button

from console_colors import RED, RESET
from util import get_color_from_priority
from db import complete_reminder, get_user, delete_reminder


class ReminderView(View):
    def __init__(self, creator, remindee, title, embed=None, frequency=""):
        super().__init__(timeout=None)
        self.creator = creator
        self.remindee = remindee
        self.title = title
        self.embed = embed
        self.frequency = frequency

    @button(label="✅", style=ButtonStyle.green)
    async def complete(
            self,
            button: Button,
            inter: MessageInteraction
    ):
        if inter.user.id != self.remindee:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"This reminder is not for you!"
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        complete_reminder(self.creator, self.remindee, self.title)
        if self.embed:
            self.embed.color = get_color_from_priority("low")
            self.embed.set_footer(text="Reminder completed!")
            await inter.response.edit_message(embed=self.embed, view=None, content=None)
        else:
            creator = get_user(self.creator)
            remindee = get_user(self.remindee)
            embed = Embed(
                color=get_color_from_priority("low"),
                title="Reminder completed!",
                description=f'{remindee["display_name"]} completed "*{self.title}*" by {creator["display_name"]}'
            )
            view = UndoCompleteView(self.creator, self.remindee, self.title, self.embed)
            await inter.response.edit_message(embed=embed, view=view, content=None)
        lifecycle_cog = inter.bot.get_cog("LifecycleCog")
        if lifecycle_cog:
            await lifecycle_cog.update_presence()
        else:
            print(f"{RED}[ERROR] Lifecycle cog not found{RESET}")

    @button(label="🗑️", style=ButtonStyle.red)
    async def delete(
            self,
            button: Button,
            inter: MessageInteraction
    ):
        if inter.user.id != self.creator and inter.user.id != self.remindee:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"This reminder is not yours!"
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        embed = Embed(
            title="Are you sure?",
            description=f"Are you sure you want to delete this reminder? This will delete any future reminders. This cannot be undone.",
            color=get_color_from_priority("high"),
        )
        view = DeleteReminderView(self.creator, self.remindee, self.title, inter.message)
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)


class DeleteReminderView(View):
    def __init__(self, creator, remindee, title, original_message):
        super().__init__(timeout=None)
        self.creator = creator
        self.remindee = remindee
        self.title = title
        self.original_message = original_message

    @button(label="I'm sure", style=ButtonStyle.green)
    async def delete(
            self,
            button: Button,
            inter: MessageInteraction
    ):
        await self.original_message.edit(view=None)
        if inter.user.id != self.creator and inter.user.id != self.remindee:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"This reminder is not yours!"
            )
            await inter.response.edit_message(embed=embed, view=None)
            return
        delete_reminder(self.creator, self.remindee, self.title)
        embed = Embed(
            color=get_color_from_priority("low"),
            title="Reminder deleted!",
            description=f'Reminder for "*{self.title}*" has been deleted by {inter.user.display_name}'
        )
        await inter.response.edit_message(embed=embed, view=None)
        lifecycle_cog = inter.bot.get_cog("LifecycleCog")
        if lifecycle_cog:
            await lifecycle_cog.update_presence()
        else:
            print(f"{RED}[ERROR] Lifecycle cog not found{RESET}")


class UndoCompleteView(View):
    def __init__(self, creator, remindee, title, embed=None):
        super().__init__(timeout=None)
        self.creator = creator
        self.remindee = remindee
        self.title = title
        self.embed = embed

    @button(label="Undo", style=ButtonStyle.red)
    async def undo(
            self,
            button: Button,
            inter: MessageInteraction
    ):
        if inter.user.id != self.remindee:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"This reminder is not yours!"
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        if self.embed:
            view = ReminderView(self.creator, self.remindee, self.title, self.embed)
            await inter.edit_original_message(embed=self.embed, view=view, content=None)
        lifecycle_cog = inter.bot.get_cog("LifecycleCog")
        if lifecycle_cog:
            await lifecycle_cog.update_presence()
        else:
            print(f"{RED}[ERROR] Lifecycle cog not found{RESET}")