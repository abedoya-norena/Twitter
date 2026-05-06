import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app
import sqlite3

DB = os.path.join(os.path.dirname(__file__), '..', 'twitter_clone.db')

client = TestClient(app, raise_server_exceptions=True)

# --- SQL INJECTION ---

# Classic login bypass
r = client.post('/login', data={'username': "' OR '1'='1", 'password': "' OR '1'='1"})
assert r.url.path != '/', "SQL injection bypassed login!"
print("SQL injection login bypass: BLOCKED")

# SQL in message body
client.post('/login', data={'username': 'Mike', 'password': '524euTjrWm6uK2C5iw8mC6aNgX1JI78o'}, follow_redirects=True)
client.post('/create_message', data={'message': "'; DROP TABLE messages; --"})
r = client.get('/')
assert r.status_code == 200
con = sqlite3.connect(DB)
count = con.execute('SELECT count(*) FROM messages').fetchone()[0]
con.close()
assert count > 0, "DROP TABLE succeeded!"
print("SQL injection DROP TABLE: BLOCKED")

# SQL in username field at registration
r = client.post('/create_user', data={
    'new_username': "'; DROP TABLE users; --",
    'password': 'x', 'password2': 'x', 'age': ''
})
con = sqlite3.connect(DB)
count = con.execute('SELECT count(*) FROM users').fetchone()[0]
con.close()
assert count > 0, "DROP TABLE users succeeded!"
print("SQL injection in register: BLOCKED")

# --- XSS ---

# XSS in message
client.post('/create_message', data={'message': '<script>alert("xss")</script>'})
r = client.get('/')
assert '<script>alert' not in r.text, "XSS script tag rendered!"
assert '&lt;script&gt;' in r.text or 'alert' not in r.text
print("XSS in message body: ESCAPED")

# XSS in username
r = client.post('/create_user', data={
    'new_username': '<script>alert(1)</script>',
    'password': 'x', 'password2': 'x', 'age': ''
})
r = client.get('/')
assert '<script>alert(1)</script>' not in r.text
print("XSS in username: ESCAPED")

# --- EDGE CASES ---

# Empty message body (bypass form required attr via direct POST)
r = client.post('/create_message', data={'message': ''})
assert r.status_code in (200, 422)
print("Empty message POST: HANDLED")

# Access create_message without login
logged_out = TestClient(app, raise_server_exceptions=True)
r = logged_out.post('/create_message', data={'message': 'hack'})
assert r.status_code == 200
assert 'logged in' in r.text.lower()
print("Create message without login: BLOCKED")

# Fake cookie (non-existent user)
from starlette.testclient import TestClient as TC
fake = TC(app, raise_server_exceptions=True, cookies={'username': 'hacker_doesnt_exist'})
r = fake.post('/create_message', data={'message': 'i am hacker'})
assert r.status_code == 200
assert 'not found' in r.text.lower()
print("Fake cookie with non-existent user: BLOCKED")

# Non-numeric age
r = client.post('/create_user', data={
    'new_username': 'AgeTest', 'password': 'x', 'password2': 'x', 'age': 'abc'
})
assert r.status_code == 200
print("Non-numeric age input: HANDLED")

print()
print("All security checks passed!")
