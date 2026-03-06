import json
from pathlib import Path

CONFIG_PATH = Path("config.json")


def _load():
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps({
            "token": "YOUR_DISCORD_TOKEN_HERE",
            "low_priority_color": "90EE90",
            "medium_priority_color": "EEBF90",
            "high_priority_color": "EE9090",
            "hide_confirmation_message": "False",
            "default_timezone": "EST5EDT",
            "default_channel": "",
            "default_reminder_option": "Last"
        }, indent=4))
    return json.loads(CONFIG_PATH.read_text())


def _save(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=4))


def get_setting(key):
    data =  _load()
    return data.get(key)


def set_setting(key, value):
    data = _load()
    data[key] = value
    _save(data)


if __name__ == "__main__":
    _load()