from disnake import ButtonStyle, MessageInteraction, Embed
from disnake.ui import View, button, Button

from colors import get_color_from_priority


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

