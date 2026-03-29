import sqlite3
from typing import Optional


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect('reminders.db')
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    db.execute("PRAGMA journal_mode = WAL;")
    db.execute("PRAGMA busy_timeout = 5000;")
    return db


def create_tables():
    with get_db() as db:
        with open('schema.sql') as f:
            db.executescript(f.read())


def get_user(user_id: int) -> sqlite3.Row:
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_tz(user_id: int) -> Optional[str]:
    with get_db() as db:
        user = db.execute("SELECT tz FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            return user['tz']
        return None


def set_user(user_id, display_name, avatar_url):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO users (id, display_name, avatar_url) VALUES (?, ?, ?)",
            (user_id, display_name, avatar_url)
        )


def set_user_locale(user_id, locale):
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO users (id, locale) VALUES (?, ?)",
            (user_id, locale)
        )


def add_reminder(creator_id, remindee_id, time, frequency, title, message, priority, destination, limit, pester):
    with get_db() as db:
        db.execute(
            "INSERT INTO reminders (creator, remindee, time, frequency, title, message, priority, destination, limits, pester) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (creator_id, remindee_id, time, frequency, title, message, priority, destination, limit, pester)
        )


def get_reminders():
    with get_db() as db:
        return db.execute("SELECT * FROM reminders").fetchall()


def get_users_reminders(user_id, completed=False):
    with get_db() as db:
        if completed:
            return db.execute(
                "SELECT * FROM reminders WHERE creator = ?",
                (user_id,)
            ).fetchall()
        else:
            return db.execute(
                "SELECT * FROM reminders WHERE creator = ? AND completed = FALSE",
                (user_id,)
            ).fetchall()


def update_reminder_time(creator_id, remindee_id, time):
    with get_db() as db:
        db.execute(
            "UPDATE reminders SET time = ?, completed = FALSE WHERE creator = ? AND remindee = ?",
            (time, creator_id, remindee_id)
        )


def update_reminder_limit(creator_id, remindee_id, limit):
    with get_db() as db:
        db.execute(
            "UPDATE reminders SET limits = ? WHERE creator = ? AND remindee = ?",
            (limit, creator_id, remindee_id)
        )


def delete_reminder(creator_id, remindee_id, title):
    with get_db() as db:
        db.execute("DELETE FROM reminders WHERE creator = ? AND remindee = ? AND title = ?", (creator_id, remindee_id, title))


def complete_reminder(creator_id, remindee_id, title):
    with get_db() as db:
        db.execute("UPDATE reminders SET completed = TRUE WHERE creator = ? AND remindee = ? AND title = ?", (creator_id, remindee_id, title))


def undo_complete_reminder(creator_id, remindee_id, title):
    with get_db() as db:
        db.execute("UPDATE reminders SET completed = FALSE WHERE creator = ? AND remindee = ? AND title = ?", (creator_id, remindee_id, title))


def get_last_location(user_id):
    with get_db() as db:
        result = db.execute(
            "SELECT destination FROM reminders WHERE creator = ? AND destination != 'Direct Message'",
            (user_id,)
        ).fetchone()
        if result:
            return result
        return db.execute(
            "SELECT destination FROM reminders WHERE destination != 'Direct Message'"
        ).fetchone()


def get_previous_locations(user_id):
    with get_db() as db:
        return db.execute(
            "SELECT destination FROM reminders WHERE creator = ?",
            (user_id,)
        ).fetchall()


def is_reminder_completed(creator_id: int, remindee_id: int, title: str) -> bool:
    with get_db() as db:
        try:
            return db.execute(
                "SELECT completed FROM reminders WHERE creator = ? AND remindee = ? AND title = ?",
                (creator_id, remindee_id, title)
            ).fetchone()['completed']
        except TypeError:
            return True


if __name__ == "__main__":
    create_tables()