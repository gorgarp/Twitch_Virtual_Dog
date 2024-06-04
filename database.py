import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('twitch_dog_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dogs (
        id INTEGER PRIMARY KEY,
        user TEXT NOT NULL,
        name TEXT NOT NULL,
        breed TEXT NOT NULL,
        level INTEGER NOT NULL,
        xp INTEGER NOT NULL,
        origin_story TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tricks (
        id INTEGER PRIMARY KEY,
        dog_id INTEGER,
        trick_name TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        xp_reward INTEGER NOT NULL,
        FOREIGN KEY(dog_id) REFERENCES dogs(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        bones INTEGER NOT NULL,
        daily_streak INTEGER NOT NULL,
        last_login DATE,
        last_interaction TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS friendships (
        id INTEGER PRIMARY KEY,
        dog1_id INTEGER,
        dog2_id INTEGER,
        interactions INTEGER NOT NULL,
        FOREIGN KEY(dog1_id) REFERENCES dogs(id),
        FOREIGN KEY(dog2_id) REFERENCES dogs(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        frequency INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL
    )
    ''')

    # Populate events with initial data
    events = [
        ("park_meet", "Your dog [name] met another dog at the park! They became best friends."),
        ("found_toy", "Your dog [name] found a new toy at the park and shared it with another dog."),
        ("dog_race", "Your dog [name] competed in a race! They both had fun and earned XP!"),
        ("learned_trick", "Your dog [name] learned a new trick from another dog."),
        ("shared_treat", "Your dog [name] shared a delicious treat at the park."),
        ("tug_of_war", "Your dog [name] played a game of tug-of-war."),
        ("found_ball", "Your dog [name] helped another dog find a lost ball."),
        ("nap_time", "Your dog [name] took a nap together with another dog."),
        ("chased_butterflies", "Your dog [name] chased butterflies together."),
        ("adventure", "Your dog [name] went on an adventure through the park.")
    ]

    cursor.executemany('''
    INSERT OR IGNORE INTO events (event_type, description, frequency) VALUES (?, ?, ?)
    ''', [(event[0], event[1], 15) for event in events])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
