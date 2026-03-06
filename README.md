# reminderBot

A Python Discord bot to set and receive reminders

## Features
- Timezone aware
- Different priorities with custom colors
- Repeating reminders

## Planned Features
- Mark reminders as completed
- Completed alerts
- Group reminders
- List reminders
- Delete reminders

### Technology Stack
- Disnake (Fork of discord.py, a Discord API python wrapper)
- SQLite3
- APScheduler
- DateParser

## Installation
1. Obtain a bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
2. Clone the repository (or download the project files)
3. Create a virtual environment
    ```bash
    virtualenv .venv
   ```
4. Activate the virtual environment:
    - Windows: `.venv\Scripts\activate`
    - Unix/macOS: `source .venv/bin/activate`
5. Install dependencies
    ```bash
   pip install -r requirements.txt
   ```
6. Modify the `config.json`
    - Enter your bot token
    - Adjust default timezone and channel to your liking
7. Run the application
    ```bash
   python bot.py
   ```
   
## Usage
- `/reminder create` - Create a new reminder