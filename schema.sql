CREATE TABLE IF NOT EXISTS reminders (
    creator INTEGER,
    remindee INTEGER,
    time DATETIME,
    frequency TEXT,
    pester TEXT,
    limits INTEGER,
    title TEXT,
    message TEXT,
    priority TEXT,
    destination INTEGER,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(creator, remindee, title)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    display_name TEXT,
    avatar_url TEXT,
    locale TEXT,
    tz TEXT
);