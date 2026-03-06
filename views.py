from disnake import ButtonStyle, MessageInteraction, Embed
from disnake.ui import View, button, Button

from colors import get_color_from_priority
from db import complete_reminder, get_user


class ReminderView(View):
    def __init__(self, creator, remindee, title, embed=None):
        super().__init__(timeout=None)
        self.creator = creator
        self.remindee = remindee
        self.title = title
        self.embed = embed

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
            await inter.edit_original_message(embed=self.embed, view=None, content=None)
        else:
            creator = get_user(self.creator)
            remindee = get_user(self.remindee)
            embed = Embed(
                color=get_color_from_priority("low"),
                title="Reminder completed!",
                description=f'{remindee['display_name']} completed "*{self.title}*" by {creator['display_name']}'
            )
            await inter.edit_original_message(embed=embed, view=None, content=None)

    @button(label="🗑️", style=ButtonStyle.red)
    async def delete(
            self,
            button: Button,
            inter: MessageInteraction
    ):
        if inter.user.id != self.creator:
            embed = Embed(
                color=get_color_from_priority("high"),
                title="Error",
                description=f"This reminder is not yours!"
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return



