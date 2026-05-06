#!/usr/bin/python3
'''
Create the NeuroPulse database.
Run once: python db_create.py
'''
import sqlite3
import argparse

parser = argparse.ArgumentParser(description='Create the NeuroPulse database')
parser.add_argument('--db_file', default='twitter_clone.db')
args = parser.parse_args()

con = sqlite3.connect(args.db_file)
cur = con.cursor()

cur.execute('''
CREATE TABLE users (
    id       INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    age      INTEGER
);
''')
con.commit()

cur.execute('''
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY,
    sender_id  INTEGER NOT NULL,
    message    TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);
''')
con.commit()

users = [
    ('Trump',   'Trump',                          78),
    ('Biden',   'Biden',                          81),
    ('Evan',    'correct horse battery staple',    7),
    ('Isaac',   'soccer',                          4),
    ('Aaron',   'guaguagua',                       3),
    ('Aurelia', '',                                1),
    ('Mike',    '524euTjrWm6uK2C5iw8mC6aNgX1JI78o', 35),
    ('Kristen', 'Possible-Rich-Absolute-Battle',  None),
]
cur.executemany(
    'INSERT INTO users (username, password, age) VALUES (?, ?, ?)',
    users
)
con.commit()

messages = [
    (1, "I'm a baby",                                                    '2021-11-14 14:30:00'),
    (2, "I'm a baby",                                                    '2021-11-14 14:30:00'),
    (3, "I'm a baby",                                                    '2021-11-14 14:33:01'),
    (4, "I'm a baby",                                                    '2021-11-15 14:35:45'),
    (3, "I'm actually a toddler",                                        '2021-11-16 14:35:45'),
    (6, 'Today in 1918, the Armistice ending WWI came into effect.',     '2021-11-11 11:00:00'),
    (6, "I'm an adult",                                                  None),
    (6, 'SQL is the best!!',                                             None),
    (7, "I'm an adult",                                                  None),
    (7, "WTF is SQL?! I thought you liked the snake thing.",             None),
    (7, 'It\'s called "Python", not the "snake thing"!',                None),
]
for sender_id, msg, ts in messages:
    if ts:
        cur.execute(
            'INSERT INTO messages (sender_id, message, created_at) VALUES (?, ?, ?)',
            (sender_id, msg, ts)
        )
    else:
        cur.execute(
            'INSERT INTO messages (sender_id, message) VALUES (?, ?)',
            (sender_id, msg)
        )
con.commit()

print(f'Database created: {args.db_file}')
