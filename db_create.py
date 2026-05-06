#!/usr/bin/python3
import sqlite3
import argparse
import random
import string
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='Create the NeuroPulse database')
parser.add_argument('--db_file', default='twitter_clone.db')
args = parser.parse_args()

random.seed(42)

con = sqlite3.connect(args.db_file)
cur = con.cursor()

cur.execute('''
CREATE TABLE users (
    id       INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    age      INTEGER,
    bio      TEXT
);
''')
con.commit()

cur.execute('''
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY,
    sender_id  INTEGER NOT NULL,
    message    TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    edited_at  TIMESTAMP,
    reply_to   INTEGER REFERENCES messages(id)
);
''')
con.commit()

# Original 8 hand-crafted users
hand_users = [
    ('Trump',   'Trump',                               78,  None),
    ('Biden',   'Biden',                               81,  None),
    ('Evan',    'correct horse battery staple',         7,  'Just a kid who loves Python'),
    ('Isaac',   'soccer',                               4,  None),
    ('Aaron',   'guaguagua',                            3,  None),
    ('Aurelia', '',                                     1,  None),
    ('Mike',    '524euTjrWm6uK2C5iw8mC6aNgX1JI78o',   35,  'Admin and SQL enthusiast. Check out https://python.org'),
    ('Kristen', 'Possible-Rich-Absolute-Battle',       None, 'Coffee and code'),
]
cur.executemany(
    'INSERT INTO users (username, password, age, bio) VALUES (?, ?, ?, ?)',
    hand_users
)
con.commit()

# Generate 192 more users to reach exactly 200
adjectives = ['fast','silent','dark','bright','neon','ghost','cyber','atomic','quantum','solar',
              'fuzzy','wild','sharp','clean','rapid','deep','cool','bold','swift','prime']
nouns      = ['node','pulse','signal','byte','wave','chip','beam','core','flux','spark',
              'loop','stack','frame','port','cache','mesh','sync','link','gate','bit']
bios = [
    'Passionate about tech and coffee',
    'Code. Sleep. Repeat.',
    'Building things on the internet',
    'Making the web a better place',
    'SQL enjoyer and Python enthusiast',
    'Full stack everything',
    'I love **markdown** and `code`',
    None, None, None,
]

used_names = {u[0] for u in hand_users}
generated_users = []
while len(generated_users) < 192:
    name = random.choice(adjectives).capitalize() + random.choice(nouns).capitalize() + str(random.randint(1, 999))
    if name in used_names:
        continue
    used_names.add(name)
    pw  = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    age = random.randint(13, 75)
    bio = random.choice(bios)
    generated_users.append((name, pw, age, bio))

cur.executemany(
    'INSERT INTO users (username, password, age, bio) VALUES (?, ?, ?, ?)',
    generated_users
)
con.commit()
print(f'Created 200 users')

# Original seed messages
seed_messages = [
    (1, "I'm a baby",                                                   '2021-11-14 14:30:00'),
    (2, "I'm a baby",                                                   '2021-11-14 14:30:00'),
    (3, "I'm a baby",                                                   '2021-11-14 14:33:01'),
    (4, "I'm a baby",                                                   '2021-11-15 14:35:45'),
    (3, "I'm actually a toddler",                                       '2021-11-16 14:35:45'),
    (6, 'Today in 1918, the Armistice ending WWI came into effect.',    '2021-11-11 11:00:00'),
    (6, "I'm an adult",                                                 None),
    (6, 'SQL is the best!!',                                            None),
    (7, "I'm an adult",                                                 None),
    (7, "WTF is SQL?! I thought you liked the snake thing.",            None),
    (7, 'It\'s called **"Python"**, not the "snake thing"!',           None),
]
for sender_id, msg, ts in seed_messages:
    if ts:
        cur.execute('INSERT INTO messages (sender_id, message, created_at) VALUES (?, ?, ?)', (sender_id, msg, ts))
    else:
        cur.execute('INSERT INTO messages (sender_id, message) VALUES (?, ?)', (sender_id, msg))
con.commit()

# Get all 200 user IDs
cur.execute('SELECT id, username FROM users')
all_users = cur.fetchall()
all_usernames = [u[1] for u in all_users]

# Message templates for bulk generation
WORDS = ['python', 'code', 'database', 'neural', 'network', 'algorithm', 'function',
         'variable', 'class', 'object', 'method', 'module', 'library', 'framework',
         'web', 'server', 'client', 'request', 'response', 'json', 'html', 'css',
         'sql', 'data', 'model', 'view', 'route', 'api', 'token', 'cookie',
         'session', 'hash', 'auth', 'test', 'debug', 'deploy', 'query',
         'table', 'column', 'key', 'cursor', 'index', 'machine', 'learning',
         'synapse', 'neuron', 'signal', 'pulse', 'memory', 'cache', 'loop', 'stack']

def rand_msg(usernames):
    w1, w2 = random.sample(WORDS, 2)
    n = random.randint(1, 10)
    mention = random.choice(usernames[:30])
    templates = [
        f"Just learned about {w1} today, it's amazing!",
        f"Hot take: {w1} is better than {w2}",
        f"I've been using {w1} for {n} years and still learning new things",
        f"Today I fixed a bug in my {w1} implementation. Took {n} hours!",
        f"Anyone have a good tutorial on {w1}?",
        f"The {w1} documentation is actually really good once you get used to it",
        f"Just deployed my {w1} app to production 🚀",
        f"Pro tip: always validate your {w1} before sending to the {w2}",
        f"Why is {w1} so complicated?? It's just a {w2}!",
        f"Check out this resource: https://docs.python.org/3/",
        f"@{mention} have you tried {w1} with {w2}?",
        f"**{w1.capitalize()}** is the future of {w2}",
        f"Hot take: `{w1}` > `{w2}`",
        f"## Thought of the day\n\n{w1.capitalize()} and {w2} are more similar than you'd think.",
        f"It's called \"{w1}\" not the \"{w2} thing\"!",
        f"Reminder: always *back up* your {w1} before running migrations",
        f"Anyone else love working with {w1}? @{mention} thoughts?",
        f"Just read a great article on {w1}: https://realpython.com",
        f"The {w1} ecosystem has grown so much. Here's my take:\n\n- Great docs\n- Active community\n- Fast iteration",
        f"POV: you're debugging a {w1} issue at 2am",
    ]
    return random.choice(templates)

def rand_ts():
    start = datetime(2024, 1, 1)
    delta = timedelta(seconds=random.randint(0, int(timedelta(days=490).total_seconds())))
    return (start + delta).strftime('%Y-%m-%d %H:%M:%S')

print('Generating 40,000 messages...')
batch = []
for user_id, _ in all_users:
    for _ in range(200):
        batch.append((user_id, rand_msg(all_usernames), rand_ts()))

cur.executemany(
    'INSERT INTO messages (sender_id, message, created_at) VALUES (?, ?, ?)',
    batch
)
con.commit()

total_msgs  = cur.execute('SELECT count(*) FROM messages').fetchone()[0]
total_users = cur.execute('SELECT count(*) FROM users').fetchone()[0]
print(f'Database ready: {total_users} users, {total_msgs} messages')
