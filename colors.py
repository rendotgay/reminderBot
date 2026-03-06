from typing import Literal

from disnake import Color

from config import get_setting


def get_color_from_priority(priority: Literal['low', 'medium', 'high']):
    hex = {
        'low': get_setting('low_priority_color'),
        'medium': get_setting('medium_priority_color'),
        'high': get_setting('high_priority_color'),
    }[priority]
    return Color(int(f"0x{hex.replace("#", "")}", 16))