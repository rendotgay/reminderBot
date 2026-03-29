# reminderBot

A Python Discord bot to set and receive reminders

## Features
- Timezone aware
- Different priorities with custom colors
- Repeating reminders
- Mark reminders as completed
- List reminders
- Pester reminders (Followup reminders if not completed)
- Reminder limits

## Planned Features
- Completed alerts
- Group reminders
- Delete reminders
- Language support

## Technology Stack
- Disnake (Fork of discord.py, a Discord API python wrapper)
- SQLite3 (Database for persistent reminders)
- APScheduler (Scheduling for recurring reminders)
- DateParser (Parse date and time from user strings)
- DateTime and PyTZ (Timezone aware datetime handling)

## Installation
### Install using built executable
1. Download the latest release from the [releases page](https://github.com/rendotgay/reminderBot/releases/)
2. Extract the archive
3. Modify the `config.json`
    - Enter your bot token
    - Adjust default timezone and channel to your liking
4. Run the executable
### Install with Python
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
- `/reminder list` - List all reminders`