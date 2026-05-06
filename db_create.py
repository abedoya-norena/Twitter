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
    'Decision neuroscience postdoc. fMRI, EEG, and too much coffee.',
    'PhD candidate. vmPFC and value-based choice. She/her.',
    'Computational psychiatry. Bayesian models of reward learning.',
    'Neuroimaging methods. SPM vs FSL discourse always welcome.',
    'Reward learning and dopamine. The **RPE signal** never gets old.',
    'Former bench scientist, now full-time scanner rat.',
    'I love `connectivity` analyses and spectral decomposition.',
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
    (1, "Just got out of the scanner. vmPFC activation was off the charts during the gambling task.",               '2021-11-14 14:30:00'),
    (2, "Counterpoint: that vmPFC signal is just salience. You haven't controlled for arousal.",                    '2021-11-14 14:30:00'),
    (3, "Both of you are wrong — it's an encoding artifact. Check your motion parameters.",                         '2021-11-14 14:33:01'),
    (4, "First day in the lab. Someone handed me a 400-page FSL manual. Send help.",                                '2021-11-15 14:35:45'),
    (3, "Four years later: I wrote the FSL manual section on GLM. It gets better.",                                 '2021-11-16 14:35:45'),
    (6, 'Reminder: the amygdala does not simply equal fear. It is a *relevance detector*. Update your slides.',     '2021-11-11 11:00:00'),
    (6, "fMRI BOLD signal is an indirect measure of neural activity. Never forget the vascular confound.",          None),
    (6, '**Loss aversion** is real, robust, and replicates at 7T. The lambda is about 2. Moving on.',               None),
    (7, "Preregistered our vmPFC valuation study. N=120. If the effect disappears I will eat my HRF.",              None),
    (7, "@Kristen what do you use for physiological noise correction in your resting-state data?",                   None),
    (7, 'It\'s called **"prediction error"**, not the "surprise thing"! — Rescorla & Wagner, 1972.',               None),
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
WORDS = ['vmPFC', 'OFC', 'amygdala', 'striatum', 'ACC', 'dlPFC', 'hippocampus',
         'insula', 'dopamine', 'serotonin', 'BOLD', 'fMRI', 'EEG', 'theta',
         'valuation', 'reward', 'prediction error', 'attention', 'inhibition',
         'connectivity', 'coupling', 'gamma oscillation', 'alpha band',
         'cortex', 'thalamus', 'prefrontal', 'nucleus accumbens', 'IFG', 'TPJ',
         'basal ganglia', 'caudate', 'putamen', 'PCC', 'dmPFC', 'loss aversion',
         'utility', 'RPE', 'VMPFC', 'HRF', 'GLM', 'ROI', 'parcellation']

def rand_msg(usernames):
    w1, w2 = random.sample(WORDS, 2)
    n = random.randint(1, 10)
    mention = random.choice(usernames[:30])
    templates = [
        f"Hot take: {w1} activity during value-based choice is epiphenomenal. The real computation is in {w2}.",
        f"{n} hours in the 7T scanner today. {w1} signal clean, head motion < 0.3 mm. Science is real.",
        f"New preprint: {w1} modulates reward prediction error via direct projections to {w2}. Link in bio.",
        f"Can we stop calling everything a 'neural correlate' and start asking about mechanisms? Especially {w1}.",
        f"The {w1}–{w2} coupling during risky choice is severely underrated. Full thread incoming.",
        f"Reviewer 2 wants us to redo the entire {w1} analysis with a different HRF. It's fine. Everything is fine.",
        f"BOLD signal in {w1} during loss trials: flat. {w2}: lit up completely. Our model is vindicated.",
        f"@{mention} what parcellation do you use for your {w1} ROI? Harvard-Oxford or a custom mask?",
        f"The dopamine {w1} signal is one of the most beautiful things in all of science. Change my mind.",
        f"Debate: is {w1} *necessary*, *sufficient*, or merely correlated with value coding in {w2}?",
        f"Our {w1} paradigm is finally ready for data collection. {n} years of piloting. Please cite us.",
        f"PSA: correct for motion in your fMRI {w1} analyses. Scrub those high-motion volumes. I beg you.",
        f"Someone already published this {w1} experiment in 2009. But we have {n * 10}x the N and better {w2} methods.",
        f"The anterior-to-posterior {w1} gradient maps onto the hierarchical {w2} model perfectly. Staring at this figure.",
        f"Found a sign flip in our {w1} contrast after {n} months. Results are identical. Make of that what you will.",
        f"Individual differences in {w1}–{w2} FC predict real-world decision quality. R=0.4{n}, p<0.001, N=1{n}2.",
        f"7T fMRI of {w1} laminar structure is genuinely mind-blowing. Sub-millimeter resolution changes everything.",
        f"The cerebellum has 70 billion neurons. When are we going to model its role in {w1} learning?",
        f"Preregistered replication of the {w1} finding in decision neuroscience: N=200, does not hold up.",
        f"Lab meeting today: does {w1} encode value or salience? {n * 10} minutes, zero consensus. Same as last month.",
        f"## New finding\n\n{w1} and {w2} show *opposite* encoding during loss aversion. Unexpected and very cool.",
        f"@{mention} have you seen the new {w1} paper? The {w2} results are wild.",
        f"Hot take: `{w1}` > `{w2}` for modeling subjective value. Fight me.",
        f"Reminder: always *preregister* your {w1} hypotheses before scanning. Especially for {w2} contrasts.",
        f"Just read: https://www.nature.com/neuro — the {w1} paper is worth your time.",
        f"POV: debugging your {w1} GLM at 2am the night before submission.",
        f"The {w1}–{w2} functional connectivity result survives leave-one-out cross-validation. We're publishing.",
        f"Asked {n} reviewers to define '{w1}'. Got {n} different answers. The field is fine.",
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
